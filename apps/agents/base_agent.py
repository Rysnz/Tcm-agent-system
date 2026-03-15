"""
Base Agent —— 所有 Agent 的公共基类。

职责：
- 提供统一的 LLM 调用接口（通过 provider_manager 路由到配置的模型）
- 失败重试与降级策略
- 链路追踪记录（写入 SessionState.agent_call_records）
- 格式化系统提示词（注入免责声明与安全约束）
"""
from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional, Tuple

from pydantic import BaseModel

from apps.agents.session_state import (
    AgentCallRecord,
    ConsultStage,
    SessionState,
)

logger = logging.getLogger("apps.agents")


# ---------------------------------------------------------------------------
# 安全系统提示词注入
# ---------------------------------------------------------------------------

_SAFETY_SYSTEM_SUFFIX = """
【安全约束 - 必须严格遵守】
1. 本系统的输出定位为"健康建议与中医辨证参考"，严禁输出任何医疗诊断结论。
2. 禁止输出明确的处方药物剂量（可提及药物名称，但须注明"请在执业中医师指导下使用"）。
3. 对未成年人、妊娠期妇女采取保守建议策略，不确定时建议就医。
4. 任何无法确定的信息必须明确标注"不确定"或"需进一步了解"。
5. 如证据不足，系统应主动追问，而非强行下结论。
6. 若检测到高风险症状（如胸痛、呼吸困难、便血、意识障碍等），必须立即建议就医，不得给出诊疗建议。
"""


def build_system_prompt(base_prompt: str, extra_constraints: str = "") -> str:
    """构建包含安全约束的系统提示词"""
    return f"{base_prompt}\n{_SAFETY_SYSTEM_SUFFIX}\n{extra_constraints}".strip()


# ---------------------------------------------------------------------------
# 基础 Agent
# ---------------------------------------------------------------------------

class BaseAgent(ABC):
    """
    所有 Agent 的公共基类。

    子类只需实现 `_execute` 方法，并通过 `run` 方法触发完整的
    重试 + 链路追踪逻辑。
    """

    # 子类必须指定
    agent_name: str = "BaseAgent"
    stage: ConsultStage = ConsultStage.INTAKE

    # 重试配置
    max_retries: int = 2
    retry_delay: float = 1.0

    def __init__(self, llm_caller=None):
        """
        Parameters
        ----------
        llm_caller : callable, optional
            签名：(messages: List[Dict], **kwargs) -> str
            若为 None，会在首次调用时尝试从 provider_manager 获取。
        """
        self._llm_caller = llm_caller

    # ------------------------------------------------------------------
    # 对外接口
    # ------------------------------------------------------------------

    def run(self, state: SessionState, **kwargs) -> SessionState:
        """
        执行 Agent，含重试与降级逻辑。

        Returns
        -------
        SessionState
            更新后的会话状态（原对象的副本）。
        """
        record = AgentCallRecord(
            agent_name=self.agent_name,
            stage=self.stage,
            started_at=datetime.utcnow(),
            input_summary=state.chief_complaint[:100] if state.chief_complaint else "",
        )

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                updated_state = self._execute(state, **kwargs)
                record.success = True
                record.finished_at = datetime.utcnow()
                record.retry_count = attempt
                if updated_state.recommendations:
                    record.output_summary = str(len(updated_state.recommendations)) + " recommendations"
                updated_state.agent_call_records.append(record)
                return updated_state
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "[%s] attempt %d/%d failed: %s",
                    self.agent_name, attempt + 1, self.max_retries + 1, exc,
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        # 全部重试失败 → 降级处理
        logger.error("[%s] all retries exhausted: %s", self.agent_name, last_error)
        record.success = False
        record.error_msg = str(last_error)
        record.finished_at = datetime.utcnow()
        record.retry_count = self.max_retries

        degraded_state = self._fallback(state)
        degraded_state.agent_call_records.append(record)
        return degraded_state

    # ------------------------------------------------------------------
    # 子类必须实现
    # ------------------------------------------------------------------

    @abstractmethod
    def _execute(self, state: SessionState, **kwargs) -> SessionState:
        """核心执行逻辑，子类实现。"""
        ...

    # ------------------------------------------------------------------
    # 降级策略（子类可覆盖）
    # ------------------------------------------------------------------

    def _fallback(self, state: SessionState) -> SessionState:
        """
        默认降级：给出保守提示并将高风险标志传递下去。
        子类可覆盖提供更具体的降级内容。
        """
        logger.warning("[%s] executing fallback strategy", self.agent_name)
        new_state = state.model_copy(deep=True)
        new_state.add_message(
            "assistant",
            f"[{self.agent_name}] 本步骤处理遇到问题，已使用保守策略。"
            "如症状持续或加重，请尽快就医。"
        )
        return new_state

    # ------------------------------------------------------------------
    # LLM 调用辅助
    # ------------------------------------------------------------------

    def _call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs,
    ) -> str:
        """
        统一的 LLM 调用封装。

        优先使用初始化时传入的 llm_caller；
        否则从 provider_manager 获取当前配置的模型。
        """
        if self._llm_caller is not None:
            return self._llm_caller(messages, temperature=temperature, max_tokens=max_tokens, **kwargs)

        # 尝试通过 provider_manager 调用
        try:
            return self._call_via_provider_manager(messages, temperature, max_tokens, **kwargs)
        except Exception as exc:
            logger.error("[%s] LLM call failed: %s", self.agent_name, exc)
            raise

    def _call_via_provider_manager(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> str:
        """通过 Django settings 中配置的 LLM 进行调用（OpenAI 兼容接口）。"""
        from django.conf import settings

        api_key = getattr(settings, "LLM_API_KEY", "")
        base_url = getattr(settings, "LLM_BASE_URL", "https://api.openai.com/v1")
        model = getattr(settings, "LLM_MODEL", "gpt-3.5-turbo")

        if not api_key:
            raise RuntimeError(
                "LLM_API_KEY 未配置。请在 .env 文件中设置 LLM_API_KEY。"
            )

        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def _call_llm_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> Generator[str, None, None]:
        """流式 LLM 调用（SSE 场景使用）。"""
        from django.conf import settings

        api_key = getattr(settings, "LLM_API_KEY", "")
        base_url = getattr(settings, "LLM_BASE_URL", "https://api.openai.com/v1")
        model = getattr(settings, "LLM_MODEL", "gpt-3.5-turbo")

        if not api_key:
            yield "[ERROR] LLM_API_KEY 未配置"
            return

        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=api_key, base_url=base_url)
        with client.chat.completions.stream(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        ) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

    # ------------------------------------------------------------------
    # 辅助：解析 LLM 输出的 JSON
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json_output(text: str) -> Dict[str, Any]:
        """
        从 LLM 输出中提取 JSON。
        支持被 ```json ... ``` 包裹的情况。
        """
        text = text.strip()
        # 去除代码块标记
        if text.startswith("```"):
            lines = text.split("\n")
            # 去掉首尾的 ```json / ``` 行
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试提取第一个 { ... } 块
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    pass
        logger.warning("Failed to parse JSON from LLM output: %s", text[:200])
        return {}
