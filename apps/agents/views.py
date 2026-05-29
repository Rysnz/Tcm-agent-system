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
import os
import re
import uuid
from datetime import datetime, timezone as dt_timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from django.utils import timezone as django_timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.agents.orchestrator import TCMOrchestrator
from apps.agents.safety_agent import SafetyGuardAgent
from apps.agents.session_state import ConsultStage, SessionState
from apps.model_provider.models import ModelConfig

logger = logging.getLogger("apps.agents")


PDF_PAGE_WIDTH = 595
PDF_PAGE_HEIGHT = 842
PDF_MARGIN_X = 48
PDF_MARGIN_TOP = 46
PDF_MARGIN_BOTTOM = 52


def _find_pdf_font(prefer_bold: bool = False) -> Optional[str]:
    """Find a local CJK-capable font for PyMuPDF PDF generation."""
    env_font = os.environ.get("TCM_REPORT_PDF_BOLD_FONT" if prefer_bold else "TCM_REPORT_PDF_FONT")
    candidates = [env_font] if env_font else []
    if prefer_bold:
        candidates.extend([
            r"C:\Windows\Fonts\msyhbd.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        ])
    candidates.extend([
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simsun.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ])
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def _clean_report_text(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("⚠️", "").replace("⚠", "").replace("\ufe0f", "")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _format_pdf_percent(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number <= 1:
        number *= 100
    return f"{round(number)}%"


def _to_local_datetime(value: Any) -> Optional[datetime]:
    """Normalize stored datetimes to the current Django timezone for display."""
    if not value:
        return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if not isinstance(value, datetime):
        return None
    if django_timezone.is_naive(value):
        value = django_timezone.make_aware(value, dt_timezone.utc)
    return django_timezone.localtime(value)


class _PdfReportBuilder:
    def __init__(self, title: str):
        import fitz

        self.fitz = fitz
        self.doc = fitz.open()
        # PyMuPDF's built-in CJK font mapping keeps Chinese text readable and
        # extractable. Latin text is drawn with Helvetica to avoid the wide
        # character spacing of the CJK font for UUIDs, dates, and dosages.
        self.regular_font_name = "china-s"
        self.bold_font_name = "china-s"
        self.ascii_font_name = "helv"
        self.ascii_bold_font_name = "hebo"
        self.regular = fitz.Font(self.regular_font_name)
        self.bold = fitz.Font(self.bold_font_name)
        self.ascii_regular = fitz.Font(self.ascii_font_name)
        self.ascii_bold = fitz.Font(self.ascii_bold_font_name)
        self.page = None
        self.y = PDF_MARGIN_TOP
        self.page_no = 0
        self.title = title
        self._new_page()

    @property
    def content_width(self) -> float:
        return PDF_PAGE_WIDTH - (PDF_MARGIN_X * 2)

    def _new_page(self) -> None:
        self.page = self.doc.new_page(width=PDF_PAGE_WIDTH, height=PDF_PAGE_HEIGHT)
        self.page_no += 1
        self.y = PDF_MARGIN_TOP

    def _font_name(self, bold: bool = False) -> str:
        return self.bold_font_name if bold else self.regular_font_name

    def _font(self, bold: bool = False):
        return self.bold if bold else self.regular

    def _font_for_char(self, char: str, bold: bool = False):
        if ord(char) < 128:
            return self.ascii_bold if bold else self.ascii_regular
        return self._font(bold)

    def _font_name_for_char(self, char: str, bold: bool = False) -> str:
        if ord(char) < 128:
            return self.ascii_bold_font_name if bold else self.ascii_font_name
        return self._font_name(bold)

    def _text_length(self, text: str, size: float, bold: bool = False) -> float:
        width = 0.0
        for char in text:
            width += self._font_for_char(char, bold).text_length(char, fontsize=size)
        return width

    def _insert_mixed_text(
        self,
        x: float,
        y: float,
        text: str,
        *,
        size: float,
        bold: bool,
        color: Tuple[float, float, float],
    ) -> None:
        if not text:
            return
        run = text[0]
        run_font_name = self._font_name_for_char(text[0], bold)
        cursor_x = x

        def flush(value: str, font_name: str, draw_x: float) -> float:
            self.page.insert_text(
                (draw_x, y),
                value,
                fontname=font_name,
                fontsize=size,
                color=color,
            )
            run_width = 0.0
            for item in value:
                run_width += self._font_for_char(item, bold).text_length(item, fontsize=size)
            return run_width

        for char in text[1:]:
            font_name = self._font_name_for_char(char, bold)
            if font_name == run_font_name:
                run += char
                continue
            cursor_x += flush(run, run_font_name, cursor_x)
            run = char
            run_font_name = font_name
        flush(run, run_font_name, cursor_x)

    def _ensure_space(self, needed: float) -> None:
        if self.y + needed <= PDF_PAGE_HEIGHT - PDF_MARGIN_BOTTOM:
            return
        self._draw_footer()
        self._new_page()

    def _draw_footer(self) -> None:
        footer = f"{self.title}  |  第 {self.page_no} 页"
        self.page.draw_line(
            (PDF_MARGIN_X, PDF_PAGE_HEIGHT - 34),
            (PDF_PAGE_WIDTH - PDF_MARGIN_X, PDF_PAGE_HEIGHT - 34),
            color=(0.86, 0.88, 0.91),
            width=0.5,
        )
        self._insert_mixed_text(
            PDF_MARGIN_X,
            PDF_PAGE_HEIGHT - 18,
            footer,
            size=8.5,
            bold=False,
            color=(0.45, 0.49, 0.56),
        )

    def _wrap_line(self, text: str, max_width: float, size: float, bold: bool = False) -> List[str]:
        text = _clean_report_text(text)
        if not text:
            return [""]
        lines: List[str] = []
        current = ""
        for char in text:
            candidate = current + char
            if current and self._text_length(candidate, size, bold) > max_width:
                lines.append(current)
                current = char.lstrip()
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines or [text]

    def add_spacer(self, height: float = 8) -> None:
        self.y += height

    def add_text(
        self,
        text: str,
        *,
        size: float = 10.2,
        bold: bool = False,
        color: Tuple[float, float, float] = (0.12, 0.16, 0.23),
        indent: float = 0,
        gap: float = 4,
        line_height_ratio: float = 1.30,
    ) -> None:
        text = _clean_report_text(text)
        if not text:
            return
        paragraphs = text.split("\n")
        line_height = size * line_height_ratio
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                self.y += line_height * 0.6
                continue
            lines = self._wrap_line(paragraph, self.content_width - indent, size, bold)
            self._ensure_space((len(lines) * line_height) + gap)
            for line in lines:
                self._insert_mixed_text(
                    PDF_MARGIN_X + indent,
                    self.y,
                    line,
                    size=size,
                    bold=bold,
                    color=color,
                )
                self.y += line_height
            self.y += gap

    def add_title(self, title: str, subtitle: str, meta_items: Sequence[Tuple[str, str]] = ()) -> None:
        top = self.y
        self.page.draw_rect(
            self.fitz.Rect(PDF_MARGIN_X, top, PDF_MARGIN_X + 5, top + 58),
            color=(0.05, 0.45, 0.30),
            fill=(0.05, 0.45, 0.30),
            width=0,
        )
        self._insert_mixed_text(
            PDF_MARGIN_X + 24,
            top + 36,
            title,
            size=22,
            bold=True,
            color=(0.04, 0.32, 0.21),
        )
        self._insert_mixed_text(
            PDF_MARGIN_X + 24,
            top + 58,
            subtitle,
            size=8.5,
            bold=False,
            color=(0.38, 0.46, 0.56),
        )

        meta_x = PDF_MARGIN_X + 290
        meta_y = top + 24
        for label, value in meta_items:
            if not value:
                continue
            self._insert_mixed_text(
                meta_x,
                meta_y,
                f"{label}：",
                size=8.7,
                bold=True,
                color=(0.29, 0.36, 0.45),
            )
            self._insert_mixed_text(
                meta_x + 54,
                meta_y,
                value,
                size=8.7,
                bold=False,
                color=(0.16, 0.20, 0.28),
            )
            meta_y += 14

        self.page.draw_line(
            (PDF_MARGIN_X, top + 76),
            (PDF_PAGE_WIDTH - PDF_MARGIN_X, top + 76),
            color=(0.78, 0.86, 0.82),
            width=0.8,
        )
        self.y = top + 84

    def add_section(self, title: str) -> None:
        self._ensure_space(64)
        self.y += 7
        self.page.draw_rect(
            self.fitz.Rect(PDF_MARGIN_X, self.y - 13, PDF_MARGIN_X + 4, self.y + 5),
            color=(0.06, 0.42, 0.28),
            fill=(0.06, 0.42, 0.28),
            width=0,
        )
        self._insert_mixed_text(
            PDF_MARGIN_X + 12,
            self.y,
            title,
            size=13,
            bold=True,
            color=(0.04, 0.34, 0.22),
        )
        self.page.draw_line(
            (PDF_MARGIN_X + 104, self.y - 4),
            (PDF_PAGE_WIDTH - PDF_MARGIN_X, self.y - 4),
            color=(0.83, 0.88, 0.85),
            width=0.5,
        )
        self.y += 10

    def add_key_values(self, items: Sequence[Tuple[str, str]]) -> None:
        for label, value in items:
            if not value:
                continue
            self.add_text(f"{label}：{value}", size=10.1, gap=1)

    def add_bullets(self, items: Sequence[str], *, indent: float = 12) -> None:
        for item in items:
            if item:
                self.add_text(f"- {item}", size=9.9, indent=indent, gap=1)

    def _notice_height(self, text: str) -> Tuple[List[str], float]:
        lines = self._wrap_line(text, self.content_width - 24, 9.2, False)
        line_height = 9.2 * 1.28
        height = max(34, 18 + len(lines) * line_height)
        return lines, height

    def add_notice(self, text: str) -> None:
        text = _clean_report_text(text)
        if not text:
            return
        text = re.sub(r"^重要提示[:：]\s*", "", text)
        lines, height = self._notice_height(text)
        line_height = 9.2 * 1.28
        self._ensure_space(height + 10)
        top = self.y + 2
        self.page.draw_rect(
            self.fitz.Rect(PDF_MARGIN_X, top, PDF_PAGE_WIDTH - PDF_MARGIN_X, top + height),
            color=(0.96, 0.84, 0.72),
            fill=(1.0, 0.97, 0.92),
            width=0.6,
        )
        self._insert_mixed_text(
            PDF_MARGIN_X + 12,
            top + 18,
            "重要提示",
            size=9.5,
            bold=True,
            color=(0.72, 0.31, 0.04),
        )
        text_y = top + 31
        for line in lines:
            self._insert_mixed_text(
                PDF_MARGIN_X + 12,
                text_y,
                line,
                size=9.2,
                bold=False,
                color=(0.72, 0.22, 0.03),
            )
            text_y += line_height
        self.y = top + height + 10

    def add_notice_section(self, title: str, text: str) -> None:
        text = _clean_report_text(text)
        if not text:
            self.add_section(title)
            return
        text = re.sub(r"^重要提示[:：]\s*", "", text)
        _, notice_height = self._notice_height(text)
        self._ensure_space(32 + notice_height + 12)
        self.add_section(title)
        self.add_notice(text)

    def finish(self) -> bytes:
        self._draw_footer()
        pdf_bytes = self.doc.tobytes(garbage=4, deflate=True)
        self.doc.close()
        return pdf_bytes


def _stage_value(stage: Any) -> str:
    if isinstance(stage, ConsultStage):
        return stage.value
    text = str(stage or "")
    if text.startswith("ConsultStage."):
        return text.split(".", 1)[1].lower()
    return text


def _last_agent_failed(state: SessionState, agent_name: str) -> bool:
    for rec in reversed(state.agent_call_records):
        if rec.agent_name == agent_name:
            return not rec.success
    return False


def _latest_agent_error(state: SessionState, agent_name: str) -> Optional[str]:
    for rec in reversed(state.agent_call_records):
        if rec.agent_name == agent_name:
            return rec.error_msg
    return None


def _is_disclaimer_message(text: str) -> bool:
    if not text:
        return False
    return ('中医智能问诊助手' in text) and ('温馨提示' in text)


def _has_active_llm_model() -> bool:
    try:
        return ModelConfig.objects.filter(  # type: ignore[attr-defined]
            is_delete=False,
            is_active=True,
            model_type='LLM',
        ).exists()
    except Exception:
        return False


def _compose_recommendation_text(state: SessionState, limit: int = 3) -> str:
    if not state.recommendations:
        return ""
    lines = ["为您整理了初步调理建议："]
    for i, rec in enumerate(state.recommendations[:limit], 1):
        lines.append(f"{i}. [{rec.category}] {rec.content}")
    lines.append("以上建议仅供健康参考，如症状持续或加重请及时就医。")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Session 持久化（使用数据库 + 缓存双写策略）
# ---------------------------------------------------------------------------

# 缓存超时常量
SESSION_CACHE_TTL = 86400          # 会话状态缓存 24 小时
WELLNESS_CHECKIN_CACHE_TTL = 86400 * 30  # 养生打卡记录缓存 30 天


def _get_session_state(session_id: str) -> Optional[SessionState]:
    """
    获取会话状态 - 优先从缓存读取，缓存未命中则从数据库读取
    """
    if not session_id:
        return None
    
    # 1. 尝试从缓存读取
    try:
        from django.core.cache import cache
        cache_key = f"agent_session:{session_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return TCMOrchestrator.restore_state(cached_data)
    except Exception as exc:
        logger.warning("Failed to get session from cache: %s", exc)
    
    # 2. 缓存未命中，从数据库读取
    try:
        from apps.agents.models import ConsultationSession
        db_session = ConsultationSession.objects.filter(session_id=session_id).first()
        if db_session and db_session.state_data:
            state = TCMOrchestrator.restore_state(db_session.state_data)
            
            # 回写到缓存
            try:
                cache.set(cache_key, db_session.state_data, timeout=SESSION_CACHE_TTL)
            except Exception:
                pass
            
            return state
    except Exception as exc:
        logger.warning("Failed to get session from database: %s", exc)
    
    return None


def _get_db_session(session_id: str):
    if not session_id:
        return None
    try:
        from apps.agents.models import ConsultationSession
        return ConsultationSession.objects.filter(session_id=session_id).first()
    except Exception as exc:
        logger.warning("Failed to load session owner: %s", exc)
        return None


def _check_session_access(
    request: Request,
    session_id: str,
    *,
    bind_anonymous: bool = False,
) -> tuple[Any, Optional[Response]]:
    """Ensure the current caller can access a consultation session."""
    db_session = _get_db_session(session_id)
    if db_session is None:
        return None, Response(
            {"error": f"会话不存在: {session_id}"},
            status=status.HTTP_404_NOT_FOUND,
        )

    owner_id = str(db_session.user_id or "").strip()
    if owner_id:
        if request.user.is_authenticated and owner_id == str(request.user.id):
            return db_session, None
        return None, Response(
            {"error": "无权访问该问诊会话"},
            status=status.HTTP_403_FORBIDDEN,
        )

    if bind_anonymous and request.user.is_authenticated:
        db_session.user_id = str(request.user.id)
        db_session.save(update_fields=["user_id"])

    return db_session, None


def _bind_session_to_request_user(session_id: str, request: Request) -> None:
    if not session_id or not request.user.is_authenticated:
        return
    db_session = _get_db_session(session_id)
    if db_session and not str(db_session.user_id or "").strip():
        db_session.user_id = str(request.user.id)
        db_session.save(update_fields=["user_id"])


def _save_session_state(state: SessionState) -> None:
    """
    保存会话状态 - 同时写入数据库和缓存
    """
    from apps.agents.orchestrator import TCMOrchestrator
    state_data = TCMOrchestrator.serialize_state(state)
    stage_value = _stage_value(state.current_stage)
    
    # 1. 写入数据库
    try:
        from apps.agents.models import ConsultationSession
        db_session, created = ConsultationSession.objects.update_or_create(
            session_id=state.session_id,
            defaults={
                'state_data': state_data,
                'current_stage': stage_value,
                'is_high_risk': state.is_high_risk,
                'chief_complaint': state.chief_complaint[:500] if state.chief_complaint else '',
                'primary_syndrome': state.primary_syndrome or '',
                'patient_age_group': state.patient_profile.age_group or '',
                'patient_gender': state.patient_profile.gender or '',
                'is_pregnant': state.patient_profile.is_pregnant,
                'is_minor': state.patient_profile.is_minor,
                'message_count': len(state.messages),
                'agent_step_count': len(state.agent_call_records),
                'is_completed': stage_value == ConsultStage.DONE.value,
            }
        )
        
        # 记录Agent执行日志
        if state.agent_call_records:
            from apps.agents.models import AgentExecutionLog
            latest_record = state.agent_call_records[-1]
            try:
                AgentExecutionLog.objects.create(
                    session=db_session,
                    agent_name=latest_record.agent_name,
                    stage=latest_record.stage,
                    started_at=latest_record.started_at,
                    finished_at=latest_record.finished_at,
                    success=latest_record.success,
                    error_message=latest_record.error_msg or '',
                    retry_count=latest_record.retry_count,
                    duration_ms=(
                        int((latest_record.finished_at - latest_record.started_at).total_seconds() * 1000)
                        if latest_record.finished_at else None
                    ),
                    input_summary=latest_record.input_summary or '',
                    output_summary=latest_record.output_summary or '',
                    trace_id=latest_record.trace_id,
                )
            except Exception as log_exc:
                logger.warning("Failed to save agent execution log: %s", log_exc)
        
    except Exception as exc:
        logger.error("Failed to save session to database: %s", exc)
    
    # 2. 写入缓存（异步，不阻塞主流程）
    try:
        from django.core.cache import cache
        cache_key = f"agent_session:{state.session_id}"
        cache.set(cache_key, state_data, timeout=SESSION_CACHE_TTL)
    except Exception as exc:
        logger.warning("Failed to save session to cache: %s", exc)


def _get_or_create_orchestrator() -> TCMOrchestrator:
    """创建编排器实例（每次请求创建，无状态）"""
    return TCMOrchestrator(session_store=_save_session_state)


# ---------------------------------------------------------------------------
# API 视图
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([AllowAny])  # 问诊功能允许匿名访问
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
    
    # 如果用户已登录，设置用户ID
    uid = str(request.user.id) if request.user.is_authenticated else ""

    # 不在这里添加欢迎消息，由IntakeAgent在首次处理时添加
    _save_session_state(state)
    
    # 更新会话的用户ID
    try:
        from apps.agents.models import ConsultationSession
        ConsultationSession.objects.filter(session_id=session_id).update(user_id=uid)
    except Exception as e:
        logger.warning(f"Failed to update session user_id: {e}")

    return Response(
        {
            "session_id": state.session_id,
            "trace_id": state.trace_id,
            "stage": state.current_stage,
            "message": "",  # 空消息，前端会显示欢迎界面
            "disclaimer": state.disclaimer,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])  # 问诊功能允许匿名访问
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

    # 输入验证
    if not user_message:
        return Response(
            {"error": "消息内容不能为空"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # 消息长度限制
    MAX_MESSAGE_LENGTH = 2000
    if len(user_message) > MAX_MESSAGE_LENGTH:
        return Response(
            {"error": f"消息内容过长，最多允许{MAX_MESSAGE_LENGTH}个字符"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # 过滤敏感内容（简单的关键词过滤）
    sensitive_keywords = ['<script', 'javascript:', 'onerror=']
    for keyword in sensitive_keywords:
        if keyword.lower() in user_message.lower():
            return Response(
                {"error": "消息包含不允许的内容"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if session_id:
        db_session = _get_db_session(session_id)
        if db_session:
            _, access_error = _check_session_access(
                request,
                session_id,
                bind_anonymous=True,
            )
            if access_error:
                return access_error
        elif not create_if_not_exists:
            return Response(
                {"error": f"会话不存在: {session_id}"},
                status=status.HTTP_404_NOT_FOUND,
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

    # 处理消息前记录计数，便于判断本轮执行结果
    assistant_count_before = sum(1 for m in state.messages if m.get("role") == "assistant")
    agent_records_before = len(state.agent_call_records)

    # 仅当满足条件时才在本轮自动生成报告
    auto_generate_report = bool(request.data.get("auto_generate_report", False))

    # 处理消息
    orchestrator = _get_or_create_orchestrator()
    try:
        state = orchestrator.process_message(state, user_message)
        _bind_session_to_request_user(state.session_id, request)
    except Exception as exc:
        logger.error("Error processing message: %s", exc)
        return Response(
            {"error": f"处理消息时发生错误: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 提取本轮新增的助手回复（优先取新增；若无新增则取最新）
    all_assistant_messages = [m for m in state.messages if m.get("role") == "assistant"]
    new_assistant_messages = all_assistant_messages[assistant_count_before:]
    if new_assistant_messages:
        latest_assistant_msg = new_assistant_messages[-1]["content"]
        # 避免把重复欢迎语当成有效问答返回
        if _is_disclaimer_message(latest_assistant_msg) and state.pending_questions:
            latest_assistant_msg = "\n".join(
                f"{i + 1}. {q}" for i, q in enumerate(state.pending_questions[:2])
            )
    elif all_assistant_messages:
        latest_assistant_msg = all_assistant_messages[-1]["content"]
    else:
        if _stage_value(state.current_stage) == ConsultStage.INQUIRY.value and state.pending_questions:
            latest_assistant_msg = "\n".join(
                f"{i + 1}. {q}" for i, q in enumerate(state.pending_questions[:2])
            )
        elif state.recommendations:
            latest_assistant_msg = _compose_recommendation_text(state)
        elif _stage_value(state.current_stage) == ConsultStage.DONE.value:
            latest_assistant_msg = state.report_text or "问诊已完成，请查看报告。"
        else:
            latest_assistant_msg = ""

    recent_records = state.agent_call_records[agent_records_before:]
    failed_record = next((r for r in recent_records if not r.success), None)

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
                "step_note": r.step_note,
            }
            for r in state.agent_call_records[-5:]  # 只返回最近5个
        ],
        # RAG 参考来源
        "reference_chunks": [
            {
                "content": chunk.content[:200],  # 限制长度
                "source": chunk.source,
                "score": chunk.score,
            }
            for chunk in state.reference_chunks[-5:]  # 只返回最近5个
        ] if state.reference_chunks else [],
    }

    if settings.DEBUG:
        response_data.update(
            {
                "debug_symptoms": [s.name for s in state.symptoms],
                "debug_inquiry_answers": state.inquiry_answers,
                "debug_chief_complaint": state.chief_complaint,
            }
        )

    if failed_record is not None:
        error_msg = failed_record.error_msg or "模型调用失败"
        response_data["assistant_message"] = (
            f"当前问诊模型调用失败（{failed_record.agent_name}），"
            f"错误信息：{error_msg}。请先在后台模型管理中修复后重试。"
        )
        response_data["model_error"] = True
    elif not _has_active_llm_model():
        response_data["assistant_message"] = (
            "当前未检测到可用的激活LLM模型，系统无法进行真实问诊推理。"
            "请先在后台模型管理中配置并激活可用模型。"
        )
        response_data["model_error"] = True
    elif not str(response_data.get("assistant_message", "")).strip():
        response_data["assistant_message"] = (
            "本轮未生成有效模型回复。请检查当前模型可用性后重试。"
        )
        response_data["model_error"] = True

    # 如果已完成，附加报告
    if auto_generate_report and _stage_value(state.current_stage) == ConsultStage.DONE.value:
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
@permission_classes([AllowAny])
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

    if session_id:
        db_session = _get_db_session(session_id)
        if db_session:
            _, access_error = _check_session_access(
                request,
                session_id,
                bind_anonymous=True,
            )
            if access_error:
                message = str(access_error.data.get("error", "无权访问"))
                def forbidden_gen():
                    yield f"data: {json.dumps({'type': 'error', 'message': message}, ensure_ascii=False)}\n\n"
                return StreamingHttpResponse(
                    forbidden_gen(), content_type="text/event-stream", status=access_error.status_code
                )

    state = _get_session_state(session_id) if session_id else None
    if state is None:
        orchestrator = _get_or_create_orchestrator()
        state = orchestrator.create_session(session_id=session_id)
        _save_session_state(state)
        _bind_session_to_request_user(state.session_id, request)

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
@permission_classes([AllowAny])
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

    if session_id:
        db_session = _get_db_session(session_id)
        if db_session:
            _, access_error = _check_session_access(
                request,
                session_id,
                bind_anonymous=True,
            )
            if access_error:
                return access_error

    # 读取图片字节
    image_bytes = image_file.read()
    
    # 获取原始文件名（用于检测文件格式）
    original_filename = image_file.name or ""
    
    # 创建临时文件用于格式检测
    import tempfile
    import os
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"tcm_tongue_{uuid.uuid4().hex}_{original_filename}")
    
    try:
        # 写入临时文件
        with open(temp_path, 'wb') as f:
            f.write(image_bytes)
        
        # 获取会话
        state = _get_session_state(session_id) if session_id else None
        if state is None:
            orchestrator = _get_or_create_orchestrator()
            state = orchestrator.create_session(session_id=session_id)
            _save_session_state(state)
            _bind_session_to_request_user(state.session_id, request)

        state.has_image = True

        # 运行 ObservationAgent，传递文件路径
        from apps.agents.observation_agent import ObservationAgent
        obs_agent = ObservationAgent()
        state = obs_agent.run(state, image_path=temp_path)
        
        # 【修复】舌象分析完成后，将阶段更新为 INQUIRY，以便用户继续问诊
        from apps.agents.session_state import ConsultStage
        state.current_stage = ConsultStage.INQUIRY
        _save_session_state(state)
    finally:
        # 清理临时文件
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

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
                "diagnosis": {
                    "summary": obs.diagnosis.summary if obs.diagnosis else "",
                    "indications": obs.diagnosis.indications if obs.diagnosis else [],
                    "suggestions": obs.diagnosis.suggestions if obs.diagnosis else [],
                },
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_session(request: Request, session_id: str) -> Response:
    """获取会话当前状态"""
    _, access_error = _check_session_access(
        request,
        session_id,
        bind_anonymous=True,
    )
    if access_error:
        return access_error

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
@permission_classes([AllowAny])
def get_report(request: Request, session_id: str) -> Response:
    """获取问诊报告"""
    _, access_error = _check_session_access(
        request,
        session_id,
        bind_anonymous=True,
    )
    if access_error:
        return access_error

    state = _get_session_state(session_id)
    if state is None:
        return Response(
            {"error": f"会话不存在: {session_id}"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if _stage_value(state.current_stage) != ConsultStage.DONE.value or not state.report_text:
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


def _extract_recommendations_for_pdf(state: SessionState) -> List[Dict[str, str]]:
    if state.recommendations:
        return [
            {
                "category": r.category or "调理建议",
                "content": r.content or "",
                "rationale": r.rationale or "",
                "caution": r.caution or "",
            }
            for r in state.recommendations
            if r.content
        ]

    report_json = state.report_json or {}
    json_recs = report_json.get("recommendations")
    if isinstance(json_recs, list) and json_recs:
        items: List[Dict[str, str]] = []
        for rec in json_recs:
            if isinstance(rec, dict):
                items.append({
                    "category": str(rec.get("category") or "调理建议"),
                    "content": str(rec.get("content") or rec.get("text") or ""),
                    "rationale": str(rec.get("rationale") or ""),
                    "caution": str(rec.get("caution") or ""),
                })
            elif rec:
                items.append({"category": "调理建议", "content": str(rec), "rationale": "", "caution": ""})
        return [item for item in items if item["content"]]

    summary = _clean_report_text(report_json.get("recommendations_summary"))
    return [{"category": "调理建议", "content": summary, "rationale": "", "caution": ""}] if summary else []


def _extract_references_for_pdf(state: SessionState) -> List[str]:
    if state.reference_chunks:
        return [
            f"{chunk.source or '知识库'}：{chunk.content[:300]}"
            for chunk in state.reference_chunks[:8]
            if chunk.content
        ]

    report_json = state.report_json or {}
    refs = report_json.get("references")
    if isinstance(refs, list) and refs:
        return [str(ref) for ref in refs if ref]

    evidence = report_json.get("evidence_chain")
    if isinstance(evidence, str) and evidence.strip():
        return [evidence.strip()]
    return []


def _extract_symptoms_for_pdf(state: SessionState) -> List[str]:
    symptoms = []
    for symptom in state.symptoms:
        detail_parts = [symptom.name]
        if symptom.duration:
            detail_parts.append(f"持续{symptom.duration}")
        if symptom.severity:
            detail_parts.append(f"程度{symptom.severity}")
        symptoms.append("，".join(detail_parts))
    return symptoms


def _generate_report_pdf(state: SessionState) -> bytes:
    report_json = state.report_json or {}
    builder = _PdfReportBuilder("中医问诊报告")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    section_no = 1
    section_nums = "一二三四五六七八九十"

    def add_numbered_section(title: str) -> None:
        nonlocal section_no
        prefix = section_nums[section_no - 1] if section_no <= len(section_nums) else str(section_no)
        builder.add_section(f"{prefix}、{title}")
        section_no += 1

    builder.add_title("中医问诊报告", "AI COPILOT / TCM CONSULTATION REPORT", [
        ("报告编号", state.session_id),
        ("生成时间", generated_at),
        ("报告性质", "健康参考建议与中医辨证参考"),
    ])

    add_numbered_section("基本信息")
    patient_summary = _clean_report_text(report_json.get("patient_summary"))
    profile = state.patient_profile
    constitution = str(profile.constitution or "").replace("ConstitutionType.", "")
    constitution = "" if constitution.upper() in {"UNKNOWN", "未知"} else constitution
    basic_items = [
        ("主诉", state.chief_complaint or report_json.get("chief_complaint") or ""),
        ("患者摘要", patient_summary),
        ("年龄段", profile.age_group or ""),
        ("性别", profile.gender or ""),
        ("体质", constitution),
    ]
    builder.add_key_values([(label, str(value)) for label, value in basic_items])

    symptoms = _extract_symptoms_for_pdf(state)
    if symptoms:
        builder.add_text("主要症状：", bold=True, gap=1)
        builder.add_bullets(symptoms)

    observation_parts = [
        state.observation.tongue_color and f"舌色：{state.observation.tongue_color}",
        state.observation.tongue_coating and f"舌苔：{state.observation.tongue_coating}",
        state.observation.coating_thickness and f"苔厚薄：{state.observation.coating_thickness}",
        state.observation.coating_texture and f"苔质：{state.observation.coating_texture}",
        state.observation.tongue_shape and f"舌形：{state.observation.tongue_shape}",
        state.observation.face_color and f"面色：{state.observation.face_color}",
    ]
    observation_text = "；".join(part for part in observation_parts if part)
    if observation_text:
        builder.add_key_values([("望诊所见", observation_text)])

    add_numbered_section("辨证结论")
    conclusion = report_json.get("syndrome_conclusion") or report_json.get("syndrome_analysis") or {}
    primary = state.primary_syndrome or (conclusion.get("primary_syndrome") if isinstance(conclusion, dict) else "")
    if primary:
        builder.add_text(f"主证型：{primary}", size=12, bold=True, color=(0.06, 0.29, 0.19), gap=3)
    if state.syndrome_candidates:
        for index, candidate in enumerate(state.syndrome_candidates, 1):
            confidence = _format_pdf_percent(candidate.confidence)
            prefix = "主证候" if index == 1 else f"候选证候 {index}"
            builder.add_text(f"{prefix}：{candidate.name}" + (f"（置信度 {confidence}）" if confidence else ""), bold=index == 1, gap=1)
            if candidate.supporting_symptoms:
                builder.add_text("支持依据：" + "、".join(candidate.supporting_symptoms), indent=12, gap=1)
            if candidate.reasoning:
                builder.add_text("辨证推理：" + candidate.reasoning, indent=12, gap=2)
    elif isinstance(conclusion, dict):
        evidence = conclusion.get("evidence") or conclusion.get("supporting_symptoms") or []
        confidence = _format_pdf_percent(conclusion.get("confidence"))
        if confidence:
            builder.add_key_values([("置信度", confidence)])
        if isinstance(evidence, list):
            builder.add_bullets([str(item) for item in evidence if item])

    add_numbered_section("调理建议")
    recommendations = _extract_recommendations_for_pdf(state)
    if recommendations:
        for index, rec in enumerate(recommendations, 1):
            builder.add_text(f"{index}. {rec['category']}", bold=True, color=(0.06, 0.29, 0.19), gap=1)
            builder.add_text(rec["content"], indent=12, gap=1)
            if rec.get("rationale"):
                builder.add_text(f"依据：{rec['rationale']}", indent=12, color=(0.40, 0.46, 0.54), gap=1)
            if rec.get("caution"):
                builder.add_text(f"注意：{rec['caution']}", indent=12, color=(0.72, 0.31, 0.04), gap=3)
    else:
        builder.add_text("暂无结构化调理建议。")

    follow_up = _clean_report_text(report_json.get("follow_up_suggestions"))
    if follow_up:
        add_numbered_section("随访建议")
        builder.add_text(follow_up)

    references = _extract_references_for_pdf(state)
    add_numbered_section("参考依据")
    if references:
        builder.add_bullets(references)
    else:
        builder.add_text("暂无可展示的知识库参考片段。")

    final_section_no = section_no
    final_prefix = section_nums[final_section_no - 1] if final_section_no <= len(section_nums) else str(final_section_no)
    section_no += 1
    disclaimer_text = (
        state.disclaimer
        or "本报告仅供健康参考与中医辨证参考，不构成医疗诊断，不能替代执业医师的专业诊疗。"
    )
    safety_texts: List[str] = []
    if state.safety_result.safety_message:
        safety_texts.append(state.safety_result.safety_message)
    safety_notes = _clean_report_text(report_json.get("safety_notes"))
    if safety_notes:
        safety_texts.append(safety_notes)

    builder.add_notice_section(f"{final_prefix}、安全提示与免责声明", "\n".join([*safety_texts, disclaimer_text]))

    return builder.finish()


@api_view(["GET"])
@permission_classes([AllowAny])
def export_report_pdf(request: Request, session_id: str) -> HttpResponse:
    """导出整理排版后的问诊报告 PDF"""
    _, access_error = _check_session_access(
        request,
        session_id,
        bind_anonymous=True,
    )
    if access_error:
        message = str(access_error.data.get("error", "无权访问该问诊会话"))
        return HttpResponse(message, status=access_error.status_code, content_type="text/plain; charset=utf-8")

    state = _get_session_state(session_id)
    if state is None:
        return HttpResponse(f"会话不存在: {session_id}", status=404, content_type="text/plain; charset=utf-8")

    if _stage_value(state.current_stage) != ConsultStage.DONE.value or not state.report_text:
        return HttpResponse("报告尚未生成，请先完成完整问诊流程", status=400, content_type="text/plain; charset=utf-8")

    try:
        pdf_bytes = _generate_report_pdf(state)
    except Exception as exc:
        logger.exception("Failed to export report PDF: %s", exc)
        return HttpResponse("PDF 导出失败", status=500, content_type="text/plain; charset=utf-8")

    filename = f"TCM_Report_{state.session_id[:8]}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@api_view(["DELETE"])
@permission_classes([AllowAny])
def delete_session(request: Request, session_id: str) -> Response:
    """删除问诊会话（真实删除）"""
    _, access_error = _check_session_access(request, session_id)
    if access_error:
        return access_error

    try:
        # 从数据库删除会话记录
        from apps.agents.models import ConsultationSession
        deleted_count, _ = ConsultationSession.objects.filter(session_id=session_id).delete()
        
        # 从缓存删除
        try:
            from django.core.cache import cache
            cache.delete(f"agent_session:{session_id}")
        except Exception:
            pass
        
        if deleted_count > 0:
            return Response(
                {"message": "会话已删除", "session_id": session_id},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": f"会话不存在: {session_id}"},
                status=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        return Response(
            {"error": f"删除会话失败: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
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
    user_id = (
        str(request.user.id)
        if request.user.is_authenticated
        else request.data.get("user_id", "anonymous")
    )

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
@permission_classes([AllowAny])
def list_user_reports(request: Request) -> Response:
    """
    获取用户的问诊报告列表（用于选择问诊报告制定养生计划）。

    Response:
    {
        "reports": [
            {
                "session_id": "...",
                "chief_complaint": "头疼、失眠",
                "primary_syndrome": "肝阳上亢证",
                "consult_time": "2026-03-23T10:00:00",
                "created_at": "2026-03-23T10:00:00",
                "report_generated_at": "2026-03-23T10:30:00",
                "summary": "..."
            }
        ]
    }
    """
    from apps.agents.models import ConsultationSession
    owner_id = str(request.user.id) if request.user.is_authenticated else ""
    sessions = ConsultationSession.objects.filter(
        is_completed=True,
        user_id=owner_id,
    ).order_by('-created_at')[:20]  # 最近20个（按问诊开始时间）
    
    reports = []
    for session in sessions:
        # 获取会话状态
        state = _get_session_state(session.session_id)
        if (state is None or _stage_value(state.current_stage) != ConsultStage.DONE.value) and session.state_data:
            try:
                state = TCMOrchestrator.restore_state(session.state_data)
            except Exception as exc:
                logger.warning("Failed to restore state_data for report list: %s", exc)
                state = None

        if state and (_stage_value(state.current_stage) == ConsultStage.DONE.value):
            consult_time = (
                _to_local_datetime(getattr(state, "first_user_message_at", None))
                or _to_local_datetime(getattr(state, "created_at", None))
                or _to_local_datetime(session.created_at)
            )
            report_time = _to_local_datetime(session.updated_at) or consult_time
            primary_syndrome = state.primary_syndrome or "待辨证"
            chief = state.chief_complaint or "未记录"
            reports.append({
                "session_id": session.session_id,
                "chief_complaint": chief,
                "primary_syndrome": primary_syndrome,
                "symptoms": [s.name for s in state.symptoms[:5]],
                "consult_time": consult_time.isoformat() if consult_time else "",
                "created_at": consult_time.isoformat() if consult_time else session.created_at.isoformat(),
                "report_generated_at": report_time.isoformat() if report_time else "",
                "updated_at": report_time.isoformat() if report_time else "",
                "summary": f"{chief[:30]} - {primary_syndrome}",
                "date_label": consult_time.strftime("%m-%d %H:%M") if consult_time else "",
            })
    
    return Response({"reports": reports})


@api_view(["GET"])
@permission_classes([AllowAny])
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
