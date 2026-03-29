"""
多智能体编排器（Orchestrator）

职责：
1. 维护 SessionState，按流程顺序调度各 Agent。
2. 在每次 Agent 执行后持久化 SessionState（通过 session_store 回调）。
3. 提供同步（单轮）和异步流式（SSE）两种执行模式。
4. 在任何阶段检测到高风险时立即触发 SafetyGuardAgent。

Agent 执行顺序（状态机）：
  INTAKE → 快速安全预检 → INQUIRY（循环直到信息充足）
  → OBSERVATION（如有图片）→ SYNDROME → RECOMMENDATION
  → SAFETY_CHECK → REPORT → DONE

流程图：
  用户输入 → IntakeAgent → SafetyGuardAgent(quick)
             ↓ 安全                 ↓ 高风险立即就医
         InquiryAgent（循环追问）
             ↓ 信息充足
         ObservationAgent（可选）
             ↓
         SyndromeAgent
             ↓
         RecommendationAgent
             ↓
         SafetyGuardAgent（完整审查）
             ↓
         ReportAgent
             ↓
         DONE
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Callable, Dict, Generator, List, Optional

from apps.agents.base_agent import BaseAgent
from apps.agents.intake_agent import IntakeAgent
from apps.agents.inquiry_agent import InquiryAgent
from apps.agents.observation_agent import ObservationAgent
from apps.agents.recommendation_agent import RecommendationAgent
from apps.agents.report_agent import ReportAgent
from apps.agents.safety_agent import SafetyGuardAgent
from apps.agents.session_state import ConsultStage, SessionState
from apps.agents.syndrome_agent import SyndromeAgent

logger = logging.getLogger("apps.agents")


def _stage_value(stage: Any) -> str:
    if isinstance(stage, ConsultStage):
        return stage.value
    text = str(stage or "")
    if text.startswith("ConsultStage."):
        name = text.split(".", 1)[1]
        return name.lower()
    return text


def _compose_recommendation_text(state: SessionState, limit: int = 3) -> str:
    if not state.recommendations:
        return ""
    lines = ["为您整理了初步调理建议："]
    for i, rec in enumerate(state.recommendations[:limit], 1):
        lines.append(f"{i}. [{rec.category}] {rec.content}")
    lines.append("以上建议仅供健康参考，如症状持续或加重请及时就医。")
    return "\n".join(lines)


class TCMOrchestrator:
    """
    中医多智能体编排器。

    Parameters
    ----------
    llm_caller : callable, optional
        LLM 调用函数，签名：(messages, **kwargs) -> str
        如果为 None，各 Agent 将通过 Django settings 的配置自动获取。
    session_store : callable, optional
        会话状态持久化回调，签名：(state: SessionState) -> None
    rag_retriever : callable, optional
        RAG 检索回调，签名：(query: str, top_k: int) -> List[ReferenceChunk]
    max_inquiry_rounds : int
        最大追问轮数，防止无限循环，默认 5。
    max_loops : int
        编排器主循环上限（防无限循环），默认 20，也可通过
        环境变量 AGENT_MAX_ORCHESTRATOR_LOOPS 覆盖。
    """

    def __init__(
        self,
        llm_caller: Optional[Callable] = None,
        session_store: Optional[Callable] = None,
        rag_retriever: Optional[Callable] = None,
        max_inquiry_rounds: int = 5,
        max_loops: int = 20,
    ):
        self.session_store = session_store
        self.max_inquiry_rounds = max_inquiry_rounds
        self._max_loops = max_loops
        
        # 循环检测配置
        self._stage_visit_counts: Dict[str, int] = {}  # 阶段访问计数
        self._max_stage_visits = 5  # 单个阶段最大访问次数

        # 初始化各 Agent
        self.intake_agent = IntakeAgent(llm_caller=llm_caller)
        self.inquiry_agent = InquiryAgent(llm_caller=llm_caller)
        self.observation_agent = ObservationAgent(llm_caller=llm_caller)
        self.syndrome_agent = SyndromeAgent(
            llm_caller=llm_caller,
            rag_retriever=rag_retriever,
        )
        self.recommendation_agent = RecommendationAgent(llm_caller=llm_caller)
        self.safety_agent_quick = SafetyGuardAgent(
            llm_caller=llm_caller,
            quick_check=True,
            stage=ConsultStage.INTAKE,  # 快速预检模式，阶段设置为 INTAKE
        )
        self.safety_agent_full = SafetyGuardAgent(
            llm_caller=llm_caller,
            quick_check=False,
        )
        self.report_agent = ReportAgent(llm_caller=llm_caller)

    # ------------------------------------------------------------------
    # 创建新会话
    # ------------------------------------------------------------------

    def create_session(self, session_id: Optional[str] = None) -> SessionState:
        """创建新的问诊会话状态"""
        state = SessionState(
            session_id=session_id or str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
        )
        self._persist(state)
        return state

    # ------------------------------------------------------------------
    # 单轮处理（用户发送一条消息）
    # ------------------------------------------------------------------

    def process_message(
        self,
        state: SessionState,
        user_message: str,
        image_bytes: Optional[bytes] = None,
        image_path: Optional[str] = None,
    ) -> SessionState:
        """
        处理用户的一条消息，推进问诊流程。

        Returns
        -------
        SessionState
            更新后的状态，包含助手回复（在 state.messages 最后）。
        """
        # 1. 添加用户消息
        state.add_message("user", user_message)
        assistant_count_before = sum(
            1 for m in state.messages if m.get("role") == "assistant"
        )

        # 2. 检测图片
        if image_bytes or image_path:
            state.has_image = True

        # 3. 根据当前阶段路由
        state = self._route(state, image_bytes=image_bytes, image_path=image_path)

        # 3.1 自动推进不需要用户继续输入的阶段，直到产出可见助手消息
        auto_progress_stages = {
            ConsultStage.OBSERVATION.value,
            ConsultStage.SYNDROME.value,
            ConsultStage.RECOMMENDATION.value,
            ConsultStage.SAFETY_CHECK.value,
        }
        auto_loops = 0
        while auto_loops < 3:
            assistant_count_now = sum(
                1 for m in state.messages if m.get("role") == "assistant"
            )
            if assistant_count_now > assistant_count_before:
                break
            if _stage_value(state.current_stage) in auto_progress_stages:
                state = self._route(state, image_bytes=image_bytes, image_path=image_path)
                auto_loops += 1
                continue
            break

        # 3.2 若流程推进后仍无新增助手消息但已有结果，合成用户可见回复
        assistant_count_now = sum(1 for m in state.messages if m.get("role") == "assistant")
        if assistant_count_now <= assistant_count_before:
            synthesized = ""
            if (
                _stage_value(state.current_stage) == ConsultStage.INQUIRY.value
                and state.pending_questions
            ):
                synthesized = "\n".join(
                    f"{i + 1}. {q}" for i, q in enumerate(state.pending_questions[:2])
                )
            elif state.recommendations:
                synthesized = _compose_recommendation_text(state)
            elif _stage_value(state.current_stage) == ConsultStage.DONE.value:
                synthesized = state.report_text or "问诊已完成，请查看报告。"

            if synthesized:
                state.add_message("assistant", synthesized)

        # 4. 持久化
        self._persist(state)

        return state

    # ------------------------------------------------------------------
    # 完整问诊流（一次性执行到完成）
    # ------------------------------------------------------------------

    def run_full_consultation(
        self,
        state: SessionState,
        image_bytes: Optional[bytes] = None,
        image_path: Optional[str] = None,
    ) -> SessionState:
        """
        执行完整问诊流程直到 DONE 状态。
        适用于信息已经足够的场景（如批量测试）。
        """
        max_loops = int(
            getattr(self, "_max_loops", 0)
            or __import__("os").environ.get("AGENT_MAX_ORCHESTRATOR_LOOPS", 20)
        )
        loop_count = 0

        while state.current_stage != ConsultStage.DONE and loop_count < max_loops:
            state = self._route(state, image_bytes=image_bytes, image_path=image_path)
            self._persist(state)
            loop_count += 1

        if loop_count >= max_loops:
            logger.error("Max loop count reached in orchestrator")

        return state

    # ------------------------------------------------------------------
    # 流式生成（SSE）
    # ------------------------------------------------------------------

    def process_message_stream(
        self,
        state: SessionState,
        user_message: str,
        image_bytes: Optional[bytes] = None,
        image_path: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """
        流式处理用户消息，以 SSE 数据格式 yield 结果片段。

        每个 yield 的字符串格式：
        - data: {"type": "stage", "stage": "inquiry", "message": "..."}\n\n
        - data: {"type": "token", "content": "..."}\n\n
        - data: {"type": "done", "state": {...}}\n\n
        - data: {"type": "error", "message": "..."}\n\n
        """
        new_state: Optional[SessionState] = None
        try:
            assistant_count_before = sum(
                1 for m in state.messages if m.get("role") == "assistant"
            )
            agent_records_before = len(state.agent_call_records)

            state.add_message("user", user_message)
            if image_bytes or image_path:
                state.has_image = True

            # 发送阶段通知
            yield self._sse_event(
                "stage",
                {
                    "stage": _stage_value(state.current_stage),
                    "message": f"正在进行：{_stage_value(state.current_stage)}",
                }
            )

            # 执行路由
            new_state = self._route(
                state, image_bytes=image_bytes, image_path=image_path
            )
            if len(new_state.agent_call_records) > agent_records_before:
                for rec in new_state.agent_call_records[agent_records_before:]:
                    yield self._sse_event(
                        "agent_step",
                        {
                            "agent": rec.agent_name,
                            "stage": _stage_value(rec.stage),
                            "success": rec.success,
                            "retry_count": rec.retry_count,
                            "step_note": rec.step_note,
                        },
                    )

            # 自动推进轻量阶段并持续发送stage事件
            # INTAKE 和 INQUIRY 不自动推进，等待用户输入
            auto_progress_stages = {
                ConsultStage.OBSERVATION.value,
                ConsultStage.SYNDROME.value,
                ConsultStage.RECOMMENDATION.value,
                ConsultStage.SAFETY_CHECK.value,
                ConsultStage.REPORT.value,
            }
            auto_loops = 0
            while _stage_value(new_state.current_stage) in auto_progress_stages and auto_loops < 3:
                yield self._sse_event(
                    "stage",
                    {
                        "stage": _stage_value(new_state.current_stage),
                        "message": f"正在进行：{_stage_value(new_state.current_stage)}",
                    },
                )
                before_loop_records = len(new_state.agent_call_records)
                new_state = self._route(new_state, image_bytes=image_bytes, image_path=image_path)
                if len(new_state.agent_call_records) > before_loop_records:
                    for rec in new_state.agent_call_records[before_loop_records:]:
                        yield self._sse_event(
                            "agent_step",
                            {
                                "agent": rec.agent_name,
                                "stage": _stage_value(rec.stage),
                                "success": rec.success,
                                "retry_count": rec.retry_count,
                                "step_note": rec.step_note,
                            },
                        )
                auto_loops += 1

            # 找到最新的助手回复并流式返回
            assistant_messages = [
                m for m in new_state.messages if m.get("role") == "assistant"
            ]
            new_assistant_messages = assistant_messages[assistant_count_before:]
            if new_assistant_messages:
                latest = new_assistant_messages[-1]["content"]
                # 以块的方式发送（模拟流式）
                chunk_size = 50
                for i in range(0, len(latest), chunk_size):
                    chunk = latest[i:i + chunk_size]
                    yield self._sse_event("token", {"content": chunk})

            assistant_messages = [m for m in new_state.messages if m.get("role") == "assistant"]
            if len(assistant_messages) > assistant_count_before:
                latest_assistant_msg = assistant_messages[-1].get("content", "")
            else:
                # 【修复】根据当前阶段返回合适的回复
                if _stage_value(new_state.current_stage) == ConsultStage.DONE.value:
                    # 问诊完成，返回报告
                    latest_assistant_msg = new_state.report_text or "问诊已完成，请查看报告。"
                elif (
                    _stage_value(new_state.current_stage) == ConsultStage.INQUIRY.value
                    and new_state.pending_questions
                ):
                    # 有待回答的问题，返回追问
                    latest_assistant_msg = "\n".join(
                        f"{i + 1}. {q}" for i, q in enumerate(new_state.pending_questions[:2])
                    )
                elif new_state.recommendations:
                    # 有调理建议，说明已经完成辨证和建议生成
                    # 返回完整的问诊结果（患者信息 + 辨证分析 + 调理建议）
                    lines = []
                    
                    # 患者信息
                    if new_state.chief_complaint:
                        lines.append(f"👤 患者信息")
                        lines.append(f"主诉：{new_state.chief_complaint}")
                        if new_state.symptoms:
                            lines.append(f"症状：{', '.join(s.name for s in new_state.symptoms[:5])}")
                        lines.append("")
                    
                    # 辨证分析
                    if new_state.syndrome_candidates:
                        lines.append("🎯 辨证结论")
                        primary = new_state.syndrome_candidates[0]
                        lines.append(f"主证型：{primary.name}")
                        if primary.confidence:
                            lines.append(f"置信度：{primary.confidence:.0%}")
                        if primary.supporting_symptoms:
                            lines.append("支持依据：")
                            for ev in primary.supporting_symptoms[:5]:
                                lines.append(f"  • {ev}")
                        if primary.reasoning:
                            lines.append(f"辨证分析：{primary.reasoning}")
                        lines.append("")
                    elif new_state.primary_syndrome:
                        lines.append("🎯 辨证结论")
                        lines.append(f"主证型：{new_state.primary_syndrome}")
                        lines.append("")
                    # 调理建议
                    lines.append("📌 详细建议")
                    for rec in new_state.recommendations[:5]:
                        lines.append(f"[{rec.category}] {rec.content}")
                    lines.append("")
                    lines.append("以上建议仅供健康参考，如症状持续或加重请及时就医。")
                    latest_assistant_msg = "\n".join(lines)
                else:
                    latest_assistant_msg = ""

            if latest_assistant_msg and len(assistant_messages) <= assistant_count_before:
                new_state.add_message("assistant", latest_assistant_msg)

            recent_records = new_state.agent_call_records[agent_records_before:]
            failed_record = next((r for r in recent_records if not r.success), None)
            model_error = bool(failed_record or not str(latest_assistant_msg or "").strip())
            if failed_record is not None:
                error_msg = failed_record.error_msg or "模型调用失败"
                latest_assistant_msg = (
                    f"当前问诊模型调用失败（{failed_record.agent_name}），"
                    f"错误信息：{error_msg}。请先在后台模型管理中修复后重试。"
                )
            elif not str(latest_assistant_msg or "").strip():
                latest_assistant_msg = "本轮未生成有效模型回复。请检查当前模型可用性后重试。"

            # 兜底：确保完成阶段优先返回完整报告文本
            if _stage_value(new_state.current_stage) == ConsultStage.DONE.value and new_state.report_text:
                latest_assistant_msg = new_state.report_text
                model_error = False

            # 确保持久化包含本轮最终助手消息
            self._persist(new_state)

            # 发送完成事件（包含状态快照）
            yield self._sse_event("done", {
                "stage": _stage_value(new_state.current_stage),
                "is_high_risk": new_state.is_high_risk,
                "pending_questions": new_state.pending_questions,
                "primary_syndrome": new_state.primary_syndrome,
                "session_id": new_state.session_id,
                "assistant_message": latest_assistant_msg,
                "model_error": model_error,
                "agent_steps": [
                    {
                        "agent": r.agent_name,
                        "stage": _stage_value(r.stage),
                        "success": r.success,
                        "retry_count": r.retry_count,
                        "step_note": r.step_note,
                    }
                    for r in new_state.agent_call_records[-5:]
                ],
            })

        except Exception as exc:
            logger.error("Orchestrator stream error: %s", exc)
            yield self._sse_event("error", {"message": str(exc)})
        finally:
            if new_state is not None:
                try:
                    self._persist(new_state)
                except Exception as persist_exc:
                    logger.warning("Stream final persist failed: %s", persist_exc)

    # ------------------------------------------------------------------
    # 核心路由逻辑
    # ------------------------------------------------------------------

    def _route(
        self,
        state: SessionState,
        image_bytes: Optional[bytes] = None,
        image_path: Optional[str] = None,
    ) -> SessionState:
        """根据当前阶段执行对应 Agent，包含循环检测"""

        stage = _stage_value(state.current_stage)
        
        # 循环检测：记录阶段访问次数
        self._stage_visit_counts[stage] = self._stage_visit_counts.get(stage, 0) + 1
        
        # 检测循环：如果某个阶段访问次数过多，强制推进
        if self._stage_visit_counts.get(stage, 0) > self._max_stage_visits:
            logger.warning(
                "Stage '%s' visited %d times, forcing progression to avoid loop",
                stage, self._stage_visit_counts[stage]
            )
            # 强制推进到下一个阶段
            next_stage = self._get_next_stage(stage)
            state.current_stage = next_stage
            self._stage_visit_counts[stage] = 0  # 重置计数
            return state

        if stage == ConsultStage.INTAKE.value:
            # 接诊
            state = self.intake_agent.run(state)
            # 快速安全预检（仅关键词扫描，不调 LLM）
            state = self.safety_agent_quick.run(state)
            # 如果快速预检触发高风险，直接生成报告
            if state.is_high_risk:
                state.current_stage = ConsultStage.REPORT
                state = self.report_agent.run(state)

        elif stage == ConsultStage.INQUIRY.value:
            inquiry_rounds = sum(
                1 for r in state.agent_call_records
                if r.agent_name == "InquiryAgent"
            )
            if inquiry_rounds >= self.max_inquiry_rounds:
                # 超过最大追问轮数，强制推进
                logger.warning("Max inquiry rounds reached, forcing progression")
                state.current_stage = ConsultStage.SYNDROME
            else:
                state = self.inquiry_agent.run(state)

        elif stage == ConsultStage.OBSERVATION.value:
            state = self.observation_agent.run(
                state,
                image_bytes=image_bytes,
                image_path=image_path,
            )

        elif stage == ConsultStage.SYNDROME.value:
            state = self.syndrome_agent.run(state)

        elif stage == ConsultStage.RECOMMENDATION.value:
            state = self.recommendation_agent.run(state)

        elif stage == ConsultStage.SAFETY_CHECK.value:
            state = self.safety_agent_full.run(state, enable_llm_review=False)
            # 安全审查后推进到REPORT阶段（而不是回退到RECOMMENDATION，避免循环）
            state.current_stage = ConsultStage.REPORT

        elif stage == ConsultStage.REPORT.value:
            state = self.report_agent.run(state)

        elif stage == ConsultStage.DONE.value:
            pass  # 已完成，无需操作

        else:
            logger.error("Unknown stage: %s", stage)

        return state

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def _persist(self, state: SessionState) -> None:
        """持久化会话状态"""
        if self.session_store:
            try:
                self.session_store(state)
                logger.info(f"Successfully persisted session state for {state.session_id}, stage={state.current_stage}")
            except Exception as exc:
                logger.error(f"Failed to persist session state: {exc}", exc_info=True)
        else:
            logger.warning(f"No session_store configured, skipping persistence for {state.session_id}")

    @staticmethod
    def _sse_event(event_type: str, data: Dict[str, Any]) -> str:
        """生成 SSE 格式的事件字符串"""
        payload = json.dumps({"type": event_type, **data}, ensure_ascii=False)
        return f"data: {payload}\n\n"
    
    def _get_next_stage(self, current_stage: str) -> ConsultStage:
        """获取下一个阶段（用于循环检测时的强制推进）"""
        stage_order = [
            ConsultStage.INTAKE.value,
            ConsultStage.INQUIRY.value,
            ConsultStage.OBSERVATION.value,
            ConsultStage.SYNDROME.value,
            ConsultStage.RECOMMENDATION.value,
            ConsultStage.SAFETY_CHECK.value,
            ConsultStage.REPORT.value,
            ConsultStage.DONE.value,
        ]
        
        try:
            current_idx = stage_order.index(current_stage)
            if current_idx < len(stage_order) - 1:
                return ConsultStage(stage_order[current_idx + 1])
        except ValueError:
            pass
        
        # 默认推进到完成阶段
        return ConsultStage.DONE

    # ------------------------------------------------------------------
    # 从 JSON 恢复状态
    # ------------------------------------------------------------------

    @staticmethod
    def restore_state(state_json: Dict[str, Any]) -> SessionState:
        """从 JSON 字典恢复 SessionState（用于会话持久化恢复）"""
        return SessionState.model_validate(state_json)

    @staticmethod
    def serialize_state(state: SessionState) -> Dict[str, Any]:
        """将 SessionState 序列化为 JSON 字典"""
        return state.model_dump(mode="json")
