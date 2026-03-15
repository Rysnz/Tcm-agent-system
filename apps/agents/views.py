"""
多智能体 API 视图

提供以下端点：
- POST /api/v2/consult/session/           创建新问诊会话
- POST /api/v2/consult/message/           发送消息（推进问诊流程）
- POST /api/v2/consult/message/stream/    流式发送消息（SSE）
- POST /api/v2/consult/image/             上传舌象图片触发望诊
- GET  /api/v2/consult/session/<id>/      获取会话状态
- GET  /api/v2/consult/session/<id>/report/  获取问诊报告
- POST /api/v2/consult/safety-check/      单独触发安全检查（调试用）
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, Optional

from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from apps.agents.orchestrator import TCMOrchestrator
from apps.agents.safety_agent import SafetyGuardAgent
from apps.agents.session_state import ConsultStage, SessionState

logger = logging.getLogger("apps.agents")

# 缓存超时常量
SESSION_CACHE_TTL = 86400          # 会话状态缓存 24 小时
WELLNESS_CHECKIN_CACHE_TTL = 86400 * 30  # 养生打卡记录缓存 30 天


# ---------------------------------------------------------------------------
# Session 持久化（使用 Django cache 或 DB，此处用 cache 做演示）
# ---------------------------------------------------------------------------

def _get_session_state(session_id: str) -> Optional[SessionState]:
    """从 Django cache 获取会话状态"""
    try:
        from django.core.cache import cache
        data = cache.get(f"agent_session:{session_id}")
        if data:
            return TCMOrchestrator.restore_state(data)
    except Exception as exc:
        logger.warning("Failed to get session from cache: %s", exc)
    return None


def _save_session_state(state: SessionState) -> None:
    """保存会话状态到 Django cache（24小时TTL）"""
    try:
        from django.core.cache import cache
        cache.set(
            f"agent_session:{state.session_id}",
            TCMOrchestrator.serialize_state(state),
            timeout=SESSION_CACHE_TTL,
        )
    except Exception as exc:
        logger.warning("Failed to save session to cache: %s", exc)


def _get_or_create_orchestrator() -> TCMOrchestrator:
    """创建编排器实例（每次请求创建，无状态）"""
    return TCMOrchestrator(session_store=_save_session_state)


# ---------------------------------------------------------------------------
# API 视图
# ---------------------------------------------------------------------------

@api_view(["POST"])
def create_session(request: Request) -> Response:
    """
    创建新问诊会话。

    Request body（可选）:
    {
        "session_id": "自定义会话ID（可选）"
    }

    Response:
    {
        "session_id": "...",
        "trace_id": "...",
        "stage": "intake",
        "greeting": "欢迎语"
    }
    """
    session_id = request.data.get("session_id") or str(uuid.uuid4())
    orchestrator = _get_or_create_orchestrator()
    state = orchestrator.create_session(session_id=session_id)

    greeting = (
        "您好！我是中医智能问诊助手。请描述您目前的主要不适或症状，"
        "我将通过系统化的问诊帮您进行中医辨证分析，提供健康建议参考。\n\n"
        "⚠️ 温馨提示：本系统提供的是健康参考建议，不构成医疗诊断，"
        "如有急重症状请立即就医。"
    )
    state.add_message("assistant", greeting)
    _save_session_state(state)

    return Response(
        {
            "session_id": state.session_id,
            "trace_id": state.trace_id,
            "stage": state.current_stage,
            "message": greeting,
            "disclaimer": state.disclaimer,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def send_message(request: Request) -> Response:
    """
    发送消息，推进问诊流程。

    Request body:
    {
        "session_id": "...",
        "message": "用户消息内容",
        "create_if_not_exists": true  （可选，默认true）
    }

    Response:
    {
        "session_id": "...",
        "stage": "inquiry",
        "is_high_risk": false,
        "assistant_message": "助手回复",
        "pending_questions": [],
        "primary_syndrome": null,
        "report": null,
        "agent_steps": [...]
    }
    """
    session_id = request.data.get("session_id")
    user_message = request.data.get("message", "").strip()
    create_if_not_exists = request.data.get("create_if_not_exists", True)

    if not user_message:
        return Response(
            {"error": "消息内容不能为空"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 获取或创建会话
    state = _get_session_state(session_id) if session_id else None
    if state is None:
        if create_if_not_exists or not session_id:
            orchestrator = _get_or_create_orchestrator()
            state = orchestrator.create_session(session_id=session_id)
        else:
            return Response(
                {"error": f"会话不存在: {session_id}"},
                status=status.HTTP_404_NOT_FOUND,
            )

    # 处理消息
    orchestrator = _get_or_create_orchestrator()
    try:
        state = orchestrator.process_message(state, user_message)
    except Exception as exc:
        logger.error("Error processing message: %s", exc)
        return Response(
            {"error": f"处理消息时发生错误: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 提取最新的助手回复
    assistant_messages = [
        m for m in state.messages if m.get("role") == "assistant"
    ]
    latest_assistant_msg = assistant_messages[-1]["content"] if assistant_messages else ""

    # 构建响应
    response_data: Dict[str, Any] = {
        "session_id": state.session_id,
        "trace_id": state.trace_id,
        "stage": state.current_stage,
        "is_high_risk": state.is_high_risk,
        "assistant_message": latest_assistant_msg,
        "pending_questions": state.pending_questions,
        "primary_syndrome": state.primary_syndrome,
        "agent_steps": [
            {
                "agent": r.agent_name,
                "stage": r.stage,
                "success": r.success,
                "retry_count": r.retry_count,
            }
            for r in state.agent_call_records[-5:]  # 只返回最近5个
        ],
    }

    # 如果已完成，附加报告
    if state.current_stage == ConsultStage.DONE:
        response_data["report"] = {
            "text": state.report_text,
            "json": state.report_json,
            "syndrome_candidates": [
                {
                    "name": c.name,
                    "confidence": c.confidence,
                    "supporting_symptoms": c.supporting_symptoms,
                }
                for c in state.syndrome_candidates
            ],
            "recommendations": [
                {
                    "category": r.category,
                    "content": r.content,
                    "rationale": r.rationale,
                    "caution": r.caution,
                }
                for r in state.recommendations
            ],
            "references": [
                {
                    "content": c.content[:200],
                    "source": c.source,
                    "score": c.score,
                }
                for c in state.reference_chunks[:5]
            ],
            "safety": {
                "risk_level": state.safety_result.risk_level,
                "should_refer_immediately": state.safety_result.should_refer_immediately,
                "safety_message": state.safety_result.safety_message,
                "special_population_flags": state.safety_result.special_population_flags,
            },
            "disclaimer": state.disclaimer,
        }

    return Response(response_data)


@api_view(["POST"])
def send_message_stream(request: Request) -> StreamingHttpResponse:
    """
    流式发送消息（SSE）。

    Request body: 同 send_message

    Response: text/event-stream，每条事件格式：
    data: {"type": "stage/token/done/error", ...}\n\n
    """
    session_id = request.data.get("session_id")
    user_message = request.data.get("message", "").strip()

    if not user_message:
        def error_gen():
            yield 'data: {"type": "error", "message": "消息内容不能为空"}\n\n'
        return StreamingHttpResponse(
            error_gen(), content_type="text/event-stream"
        )

    state = _get_session_state(session_id) if session_id else None
    if state is None:
        orchestrator = _get_or_create_orchestrator()
        state = orchestrator.create_session(session_id=session_id)

    orchestrator = _get_or_create_orchestrator()

    def event_stream():
        try:
            for event in orchestrator.process_message_stream(state, user_message):
                yield event
        except Exception as exc:
            logger.error("Stream error: %s", exc)
            yield f'data: {{"type": "error", "message": "{exc}"}}\n\n'

    response = StreamingHttpResponse(
        event_stream(), content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@api_view(["POST"])
@parser_classes([MultiPartParser, JSONParser])
def upload_tongue_image(request: Request) -> Response:
    """
    上传舌象图片，触发 ObservationAgent 分析。

    Request: multipart/form-data
    - session_id: 会话ID
    - image: 图片文件

    Response:
    {
        "session_id": "...",
        "observation": { "tongue_color": "...", ... },
        "image_features": [...]
    }
    """
    session_id = request.data.get("session_id")
    image_file = request.FILES.get("image")

    if not image_file:
        return Response(
            {"error": "请上传图片文件"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 读取图片字节
    image_bytes = image_file.read()

    # 获取会话
    state = _get_session_state(session_id) if session_id else None
    if state is None:
        orchestrator = _get_or_create_orchestrator()
        state = orchestrator.create_session(session_id=session_id)

    state.has_image = True

    # 运行 ObservationAgent
    from apps.agents.observation_agent import ObservationAgent
    obs_agent = ObservationAgent()
    state = obs_agent.run(state, image_bytes=image_bytes)
    _save_session_state(state)

    obs = state.observation
    return Response(
        {
            "session_id": state.session_id,
            "observation": {
                "tongue_color": obs.tongue_color,
                "tongue_coating": obs.tongue_coating,
                "coating_thickness": obs.coating_thickness,
                "coating_texture": obs.coating_texture,
                "tongue_shape": obs.tongue_shape,
                "face_color": obs.face_color,
                "image_features": obs.image_features,
            },
        }
    )


@api_view(["GET"])
def get_session(request: Request, session_id: str) -> Response:
    """获取会话当前状态"""
    state = _get_session_state(session_id)
    if state is None:
        return Response(
            {"error": f"会话不存在: {session_id}"},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(
        {
            "session_id": state.session_id,
            "stage": state.current_stage,
            "is_high_risk": state.is_high_risk,
            "chief_complaint": state.chief_complaint,
            "primary_syndrome": state.primary_syndrome,
            "pending_questions": state.pending_questions,
            "symptoms": [s.model_dump() for s in state.symptoms],
            "patient_profile": state.patient_profile.model_dump(),
            "messages_count": len(state.messages),
            "agent_steps_count": len(state.agent_call_records),
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
        }
    )


@api_view(["GET"])
def get_report(request: Request, session_id: str) -> Response:
    """获取问诊报告"""
    state = _get_session_state(session_id)
    if state is None:
        return Response(
            {"error": f"会话不存在: {session_id}"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if state.current_stage != ConsultStage.DONE or not state.report_text:
        return Response(
            {
                "error": "报告尚未生成",
                "current_stage": state.current_stage,
                "hint": "需要完成完整问诊流程后才能获取报告",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "session_id": state.session_id,
            "report_text": state.report_text,
            "report_json": state.report_json,
            "syndrome_candidates": [
                {
                    "name": c.name,
                    "confidence": c.confidence,
                    "supporting_symptoms": c.supporting_symptoms,
                    "sources": c.sources,
                }
                for c in state.syndrome_candidates
            ],
            "recommendations": [
                {
                    "category": r.category,
                    "content": r.content,
                    "rationale": r.rationale,
                    "caution": r.caution,
                }
                for r in state.recommendations
            ],
            "references": [
                {
                    "content": c.content[:300],
                    "source": c.source,
                    "score": c.score,
                }
                for c in state.reference_chunks[:8]
            ],
            "safety": {
                "risk_level": state.safety_result.risk_level,
                "should_refer_immediately": state.safety_result.should_refer_immediately,
                "safety_message": state.safety_result.safety_message,
            },
            "evidence_chain": {
                "chief_complaint": state.chief_complaint,
                "symptoms": [s.name for s in state.symptoms],
                "inquiry_answers": state.inquiry_answers,
                "observation": {
                    "tongue_color": state.observation.tongue_color,
                    "tongue_coating": state.observation.tongue_coating,
                },
                "primary_syndrome": state.primary_syndrome,
                "syndrome_confidence": (
                    state.syndrome_candidates[0].confidence
                    if state.syndrome_candidates else None
                ),
            },
            "agent_trace": [
                {
                    "agent": r.agent_name,
                    "stage": r.stage,
                    "success": r.success,
                    "duration_ms": (
                        int((r.finished_at - r.started_at).total_seconds() * 1000)
                        if r.finished_at else None
                    ),
                }
                for r in state.agent_call_records
            ],
            "disclaimer": state.disclaimer,
        }
    )


@api_view(["POST"])
def safety_check(request: Request) -> Response:
    """
    单独触发安全检查（用于调试或前置过滤）。

    Request body:
    {
        "text": "待检查的文本内容",
        "is_pregnant": false,
        "is_minor": false
    }

    Response:
    {
        "risk_level": "low/medium/high/critical",
        "triggered_keywords": [...],
        "should_refer_immediately": false,
        "safety_message": null
    }
    """
    text = request.data.get("text", "")
    if not text:
        return Response(
            {"error": "请提供待检查的文本"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 创建临时状态
    state = SessionState()
    state.chief_complaint = text
    state.patient_profile.is_pregnant = request.data.get("is_pregnant", False)
    state.patient_profile.is_minor = request.data.get("is_minor", False)

    # 快速安全检查
    agent = SafetyGuardAgent(quick_check=True)
    state = agent.run(state)

    return Response(
        {
            "risk_level": state.safety_result.risk_level,
            "triggered_keywords": state.safety_result.triggered_keywords,
            "special_population_flags": state.safety_result.special_population_flags,
            "should_refer_immediately": state.safety_result.should_refer_immediately,
            "safety_message": state.safety_result.safety_message,
        }
    )


# ---------------------------------------------------------------------------
# 个性化养生管理 API
# ---------------------------------------------------------------------------

@api_view(["POST"])
def generate_wellness_plan(request: Request) -> Response:
    """
    生成个性化养生计划。

    Request body:
    {
        "constitution": "气虚质",
        "start_date": "2026-01-01",  （可选，默认今天）
        "cycle_days": 7,              （可选，默认7天）
        "previous_checkins": [...]   （可选，上期打卡记录）
    }

    Response:
    {
        "plan": { ... },
        "summary_text": "..."
    }
    """
    from datetime import date
    from apps.agents.wellness import (
        CheckInRecord,
        WellnessPlanGenerator,
        CONSTITUTION_PLANS,
    )

    constitution = request.data.get("constitution", "平和质")
    if constitution not in CONSTITUTION_PLANS:
        return Response(
            {
                "error": f"不支持的体质类型: {constitution}",
                "supported": list(CONSTITUTION_PLANS.keys()),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    start_date_str = request.data.get("start_date")
    try:
        start_date = (
            date.fromisoformat(start_date_str) if start_date_str else date.today()
        )
    except ValueError:
        return Response(
            {"error": "日期格式错误，请使用 ISO 格式（如 2026-01-01）"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cycle_days = int(request.data.get("cycle_days", 7))
    if cycle_days < 1 or cycle_days > 30:
        return Response(
            {"error": "cycle_days 须在 1~30 之间"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 解析上期打卡记录（用于微调）
    previous_checkins_data = request.data.get("previous_checkins", [])
    previous_checkins = []
    for ci in previous_checkins_data:
        try:
            previous_checkins.append(
                CheckInRecord(
                    date=ci.get("date", ""),
                    completed_items=ci.get("completed_items", []),
                    skipped_items=ci.get("skipped_items", []),
                    energy_level=int(ci.get("energy_level", 3)),
                    sleep_quality=int(ci.get("sleep_quality", 3)),
                    mood_score=int(ci.get("mood_score", 3)),
                    notes=ci.get("notes", ""),
                )
            )
        except Exception:
            pass  # 忽略格式错误的打卡记录

    generator = WellnessPlanGenerator()
    plan = generator.generate_weekly_plan(
        constitution=constitution,
        start_date=start_date,
        cycle_days=cycle_days,
        previous_feedback=previous_checkins if previous_checkins else None,
    )
    summary = generator.generate_summary_text(plan)

    # 序列化为 dict
    from dataclasses import asdict
    plan_dict = asdict(plan)

    return Response({"plan": plan_dict, "summary_text": summary})


@api_view(["POST"])
def wellness_checkin(request: Request) -> Response:
    """
    提交养生打卡记录。

    Request body:
    {
        "user_id": "...",        （可选）
        "date": "2026-01-01",
        "completed_items": ["按时入睡", "运动30分钟"],
        "skipped_items": ["穴位保健"],
        "energy_level": 4,       1-5
        "sleep_quality": 3,      1-5
        "mood_score": 4,         1-5
        "notes": "今天状态不错"  （可选）
    }

    Response:
    {
        "success": true,
        "message": "...",
        "completion_rate": 0.75,
        "encouragement": "..."
    }
    """
    import json
    from django.core.cache import cache

    date_str = request.data.get("date", "")
    completed = request.data.get("completed_items", [])
    skipped = request.data.get("skipped_items", [])
    energy = int(request.data.get("energy_level", 3))
    sleep_q = int(request.data.get("sleep_quality", 3))
    mood = int(request.data.get("mood_score", 3))
    notes = request.data.get("notes", "")
    user_id = request.data.get("user_id", "anonymous")

    total = len(completed) + len(skipped)
    completion_rate = len(completed) / total if total > 0 else 0

    # 持久化到 cache（生产环境应持久化到数据库）
    record = {
        "date": date_str,
        "completed_items": completed,
        "skipped_items": skipped,
        "energy_level": energy,
        "sleep_quality": sleep_q,
        "mood_score": mood,
        "notes": notes,
        "completion_rate": completion_rate,
    }
    cache_key = f"wellness_checkin:{user_id}:{date_str}"
    cache.set(cache_key, record, timeout=WELLNESS_CHECKIN_CACHE_TTL)

    # 生成鼓励语
    if completion_rate >= 0.9:
        encouragement = "🌟 太棒了！今天完成率接近满分，继续保持！"
    elif completion_rate >= 0.7:
        encouragement = "👏 完成得不错！明天争取更好！"
    elif completion_rate >= 0.5:
        encouragement = "💪 完成了一半以上，继续努力！"
    else:
        encouragement = "😊 没关系，重要的是开始！明天继续加油！"

    return Response(
        {
            "success": True,
            "message": f"{date_str} 打卡成功",
            "completion_rate": round(completion_rate, 2),
            "encouragement": encouragement,
        }
    )


@api_view(["GET"])
def list_constitutions(request: Request) -> Response:
    """
    获取九种体质的说明和特征。

    Response:
    {
        "constitutions": [
            {
                "name": "气虚质",
                "theme": "...",
                "principles": [...],
                "diet_principles": "...",
                "forbidden_foods": [...]
            }
        ]
    }
    """
    from apps.agents.wellness import CONSTITUTION_PLANS

    constitutions = []
    for name, data in CONSTITUTION_PLANS.items():
        constitutions.append(
            {
                "name": name,
                "theme": data["theme"],
                "principles": data["principles"],
                "diet_principles": data.get("diet_principles", ""),
                "forbidden_foods": data.get("forbidden_foods", []),
                "recommended_teas": data.get("recommended_teas", []),
                "acupoints": data.get("acupoints", []),
            }
        )

    return Response({"constitutions": constitutions})
