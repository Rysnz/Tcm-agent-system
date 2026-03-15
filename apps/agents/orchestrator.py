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

        # 2. 检测图片
        if image_bytes or image_path:
            state.has_image = True

        # 3. 根据当前阶段路由
        state = self._route(state, image_bytes=image_bytes, image_path=image_path)

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
        try:
            state.add_message("user", user_message)
            if image_bytes or image_path:
                state.has_image = True

            # 发送阶段通知
            yield self._sse_event(
                "stage",
                {"stage": state.current_stage, "message": f"正在进行：{state.current_stage}"}
            )

            # 执行路由
            new_state = self._route(
                state, image_bytes=image_bytes, image_path=image_path
            )
            self._persist(new_state)

            # 找到最新的助手回复并流式返回
            assistant_messages = [
                m for m in new_state.messages if m.get("role") == "assistant"
            ]
            if assistant_messages:
                latest = assistant_messages[-1]["content"]
                # 以块的方式发送（模拟流式）
                chunk_size = 50
                for i in range(0, len(latest), chunk_size):
                    chunk = latest[i:i + chunk_size]
                    yield self._sse_event("token", {"content": chunk})

            # 发送完成事件（包含状态快照）
            yield self._sse_event("done", {
                "stage": new_state.current_stage,
                "is_high_risk": new_state.is_high_risk,
                "pending_questions": new_state.pending_questions,
                "primary_syndrome": new_state.primary_syndrome,
                "session_id": new_state.session_id,
            })

        except Exception as exc:
            logger.error("Orchestrator stream error: %s", exc)
            yield self._sse_event("error", {"message": str(exc)})

    # ------------------------------------------------------------------
    # 核心路由逻辑
    # ------------------------------------------------------------------

    def _route(
        self,
        state: SessionState,
        image_bytes: Optional[bytes] = None,
        image_path: Optional[str] = None,
    ) -> SessionState:
        """根据当前阶段执行对应 Agent"""

        stage = state.current_stage

        if stage == ConsultStage.INTAKE:
            # 接诊
            state = self.intake_agent.run(state)
            # 快速安全预检（仅关键词扫描，不调 LLM）
            state = self.safety_agent_quick.run(state)
            # 如果快速预检触发高风险，直接生成报告
            if state.is_high_risk:
                state.current_stage = ConsultStage.REPORT
                state = self.report_agent.run(state)

        elif stage == ConsultStage.INQUIRY:
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

        elif stage == ConsultStage.OBSERVATION:
            state = self.observation_agent.run(
                state,
                image_bytes=image_bytes,
                image_path=image_path,
            )

        elif stage == ConsultStage.SYNDROME:
            state = self.syndrome_agent.run(state)

        elif stage == ConsultStage.RECOMMENDATION:
            state = self.recommendation_agent.run(state)

        elif stage == ConsultStage.SAFETY_CHECK:
            state = self.safety_agent_full.run(state)
            state.current_stage = ConsultStage.REPORT

        elif stage == ConsultStage.REPORT:
            state = self.report_agent.run(state)

        elif stage == ConsultStage.DONE:
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
            except Exception as exc:
                logger.warning("Failed to persist session state: %s", exc)

    @staticmethod
    def _sse_event(event_type: str, data: Dict[str, Any]) -> str:
        """生成 SSE 格式的事件字符串"""
        payload = json.dumps({"type": event_type, **data}, ensure_ascii=False)
        return f"data: {payload}\n\n"

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
