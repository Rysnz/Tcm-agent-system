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
import re
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generator, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

from pydantic import BaseModel

from apps.agents.session_state import (
    AgentCallRecord,
    ConsultStage,
    SessionState,
)

logger = logging.getLogger("apps.agents")


# ---------------------------------------------------------------------------
# 错误类型枚举
# ---------------------------------------------------------------------------

class ErrorType(str, Enum):
    """Agent执行错误类型"""
    TECHNICAL = "technical"      # 技术错误（网络、超时、API错误）
    VALIDATION = "validation"    # 验证错误（输入格式、数据校验）
    MEDICAL = "medical"          # 医学相关错误（辨证失败、建议生成失败）
    UNKNOWN = "unknown"          # 未知错误


LIGHTWEIGHT_MODE = False


def _sanitize_reasoning_noise(text: str) -> str:
    """去除常见思维链污染，仅保留JSON主体。"""
    if not text:
        return text
    parsed = _extract_last_json_obj(text)
    if parsed is not None:
        return json.dumps(parsed, ensure_ascii=False)

    lower = text.lower()
    if "reasoning_content" in lower or "thinking process" in lower:
        # 尝试截取第一个 JSON 对象
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]
    return text


def _extract_last_json_obj(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    # 0) 先清理可能干扰的前缀文本（如 "Here is the JSON:" 等）
    text = text.strip()
    
    # 调试信息
    logger.debug(f"[JSON Extract] Input text length: {len(text)}")
    logger.debug(f"[JSON Extract] Input text preview: {text[:200]}")
    
    # 1) 整体解析
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            logger.debug(f"[JSON Extract] Successfully parsed as whole JSON")
            return obj
    except Exception as e:
        logger.debug(f"[JSON Extract] Whole JSON parse failed: {e}")

    # 2) fenced json - 优先尝试这个，因为模型经常返回```json代码块
    for m in re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE):
        snippet = m.group(1).strip()
        if not snippet:
            continue
        # 先尝试直接解析
        try:
            obj = json.loads(snippet)
            if isinstance(obj, dict):
                logger.debug(f"[JSON Extract] Successfully parsed fenced JSON")
                return obj
        except Exception as e:
            logger.debug(f"[JSON Extract] Fenced JSON parse failed: {e}")
            pass
        # 如果失败，尝试修复可能被截断的JSON
        try:
            # 补全可能缺失的结尾
            fixed = _fix_truncated_json(snippet)
            if fixed:
                obj = json.loads(fixed)
                if isinstance(obj, dict):
                    logger.debug(f"[JSON Extract] Successfully parsed fixed JSON")
                    return obj
        except Exception as e:
            logger.debug(f"[JSON Extract] Fixed JSON parse failed: {e}")
            continue

    # 3) 平衡大括号扫描，取最后一个可解析对象
    stack: List[int] = []
    candidates: List[str] = []
    for idx, ch in enumerate(text):
        if ch == "{":
            stack.append(idx)
        elif ch == "}" and stack:
            start = stack.pop()
            if not stack:
                candidates.append(text[start: idx + 1])

    for candidate in reversed(candidates):
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                logger.debug(f"[JSON Extract] Successfully parsed balanced JSON")
                return obj
        except Exception as e:
            logger.debug(f"[JSON Extract] Balanced JSON parse failed: {e}")
            # 尝试修复被截断的JSON
            try:
                fixed = _fix_truncated_json(candidate)
                if fixed:
                    obj = json.loads(fixed)
                    if isinstance(obj, dict):
                        logger.debug(f"[JSON Extract] Successfully parsed fixed balanced JSON")
                        return obj
            except Exception as e:
                logger.debug(f"[JSON Extract] Fixed balanced JSON parse failed: {e}")
                continue
    return None


def _fix_truncated_json(text: str) -> Optional[str]:
    """尝试修复被截断的JSON字符串"""
    if not text:
        return None
    
    text = text.strip()
    
    # 计算需要补全的括号
    open_braces = text.count('{')
    close_braces = text.count('}')
    open_brackets = text.count('[')
    close_brackets = text.count(']')
    
    # 检查最后一个字符
    last_char = text[-1] if text else ''
    
    # 如果以逗号结尾，移除逗号
    if last_char == ',':
        text = text[:-1]
    
    # 补全缺失的括号
    if open_brackets > close_brackets:
        text += ']' * (open_brackets - close_brackets)
    if open_braces > close_braces:
        text += '}' * (open_braces - close_braces)
    
    # 如果以引号开头但没有结尾，补全引号
    if text.count('"') % 2 != 0:
        # 找到最后一个未闭合的引号位置
        last_quote = text.rfind('"')
        if last_quote > 0:
            # 检查这个引号是否是键值对的一部分
            before_quote = text[:last_quote]
            after_quote = text[last_quote + 1:]
            # 如果引号后面没有冒号，可能是值被截断
            if ':' not in after_quote[:10]:
                text += '"'
    
    return text


def _extract_text_from_model_response(response: Any) -> str:
    """尽可能从模型响应中提取可解析文本。"""
    if response is None:
        return ""

    # LangChain AIMessage 常见路径
    content = getattr(response, "content", None)
    if isinstance(content, str) and content.strip():
        return content

    # 一些模型将思维内容放在 additional_kwargs
    additional_kwargs = getattr(response, "additional_kwargs", None)
    if isinstance(additional_kwargs, dict):
        for key in ["reasoning_content", "reasoning", "output_text", "text"]:
            value = additional_kwargs.get(key)
            if isinstance(value, str) and value.strip():
                return value

    # 字典响应兜底
    if isinstance(response, dict):
        for key in ["content", "reasoning_content", "text", "output_text"]:
            value = response.get(key)
            if isinstance(value, str) and value.strip():
                return value

    return str(response)


def _trim_context_for_local_models(messages: List[Dict[str, str]], keep_turns: int = 6) -> List[Dict[str, str]]:
    """
    压缩本地模型输入上下文，降低 token 与 KV cache 压力。
    
    优化策略：
    1. 始终保留system消息
    2. 保留最早的消息（通常包含主诉和关键信息）
    3. 保留最近的消息（当前对话上下文）
    4. 如果中间有重要内容，尝试保留
    """
    if not messages:
        return messages
    
    # 分离system消息和非system消息
    system_msgs = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]
    
    # 如果消息数量在限制内，直接返回
    if len(non_system) <= keep_turns * 2:
        return messages
    
    # 保留策略：
    # 1. 最早的2条消息（通常包含主诉和初始症状描述）
    # 2. 最近的(keep_turns-2)*2条消息
    earliest_count = min(4, len(non_system) // 4)  # 保留最早的消息
    recent_count = (keep_turns - 2) * 2  # 保留最近的消息
    
    if len(non_system) <= earliest_count + recent_count:
        return messages
    
    # 构建保留的消息列表
    kept_messages = []
    
    # 保留最早的消息
    kept_messages.extend(non_system[:earliest_count])
    
    # 添加分隔标记（如果中间有省略）
    if earliest_count > 0 and recent_count > 0:
        # 可以选择添加一个标记，但为了不破坏对话格式，这里跳过
        pass
    
    # 保留最近的消息
    kept_messages.extend(non_system[-recent_count:])
    
    return system_msgs[:1] + kept_messages


def _resolve_model_runtime(
    provider,
    model_type: str,
    model_name: str,
    model_credential: Dict[str, Any],
    **model_kwargs,
):
    """运行时模型实例解析，兼容自定义模型名"""
    try:
        return provider.get_model(model_type, model_name, model_credential, **model_kwargs)
    except Exception:
        model_info_manage = provider.get_model_info_manage()
        model_info = getattr(model_info_manage, 'default_model_dict', {}).get(model_type)
        if model_info is None:
            candidates = [
                info for info in getattr(model_info_manage, 'model_list', [])
                if getattr(info, 'model_type', None) == model_type
            ]
            model_info = candidates[0] if candidates else None
        model_class = getattr(model_info, 'model_class', None) if model_info else None
        if model_class is None:
            raise
        return model_class.new_instance(model_type, model_name, model_credential, **model_kwargs)


def _build_local_reasoning_flags() -> Dict[str, Any]:
    """本地兼容模型的最小化推理参数。"""
    # 注意：ChatOpenAI 对 `reasoning` 字段要求为 dict，
    # 传入 bool 会触发 pydantic 校验错误。
    # 为避免不同后端兼容差异，这里暂不注入 reasoning 相关参数。
    return {}


# ---------------------------------------------------------------------------
# Agent JSON Schema 定义（用于 LM Studio Structured Output）
# ---------------------------------------------------------------------------

_INTAKE_JSON_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "intake_response",
        "strict": "true",
        "schema": {
            "type": "object",
            "properties": {
                "chief_complaint": {"type": "string"},
                "symptoms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "duration": {"type": ["string", "null"]},
                            "severity": {"type": ["string", "null"]},
                            "onset": {"type": ["string", "null"]}
                        },
                        "required": ["name"]
                    }
                },
                "age_group": {"type": ["string", "null"]},
                "gender": {"type": ["string", "null"]},
                "is_pregnant": {"type": "boolean"},
                "is_minor": {"type": "boolean"},
                "medical_history": {"type": "array", "items": {"type": "string"}},
                "current_medications": {"type": "array", "items": {"type": "string"}},
                "needs_clarification": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["chief_complaint", "symptoms"]
        }
    }
}

_INQUIRY_JSON_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "inquiry_response",
        "strict": "true",
        "schema": {
            "type": "object",
            "properties": {
                "questions": {"type": "array", "items": {"type": "string"}},
                "is_sufficient": {"type": "boolean"},
                "new_symptoms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "duration": {"type": ["string", "null"]},
                            "severity": {"type": ["string", "null"]},
                            "onset": {"type": ["string", "null"]}
                        },
                        "required": ["name"]
                    }
                },
                "answered_dimensions": {"type": "array", "items": {"type": "string"}},
                "inquiry_answers": {"type": "object"}
            },
            "required": ["questions", "is_sufficient"]
        }
    }
}

_SYNDROME_JSON_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "syndrome_response",
        "strict": "true",
        "schema": {
            "type": "object",
            "properties": {
                "syndrome_candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "confidence": {"type": "number"},
                            "supporting_symptoms": {"type": "array", "items": {"type": "string"}},
                            "reasoning": {"type": "string"},
                            "classical_basis": {"type": ["string", "null"]}
                        },
                        "required": ["name", "confidence"]
                    }
                },
                "primary_syndrome": {"type": ["string", "null"]},
                "constitution_inference": {"type": ["string", "null"]},
                "insufficient_info": {"type": "array", "items": {"type": "string"}},
                "evidence_summary": {"type": "string"}
            },
            "required": ["syndrome_candidates"]
        }
    }
}

_RECOMMENDATION_JSON_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "recommendation_response",
        "strict": "true",
        "schema": {
            "type": "object",
            "properties": {
                "recommendations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string"},
                            "content": {"type": "string"},
                            "rationale": {"type": "string"},
                            "caution": {"type": ["string", "null"]}
                        },
                        "required": ["category", "content"]
                    }
                },
                "primary_syndrome": {"type": "string"},
                "overall_risk_level": {"type": "string"},
                "should_see_doctor": {"type": "boolean"},
                "follow_up_questions": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["recommendations", "primary_syndrome"]
        }
    }
}

_REPORT_JSON_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "report_response",
        "strict": "true",
        "schema": {
            "type": "object",
            "properties": {
                "patient_summary": {"type": "string"},
                "chief_complaint": {"type": "string"},
                "syndrome_analysis": {
                    "type": "object",
                    "properties": {
                        "primary_syndrome": {"type": "string"},
                        "confidence": {"type": "number"},
                        "supporting_symptoms": {"type": "array", "items": {"type": "string"}},
                        "analysis": {"type": "string"}
                    }
                },
                "recommendations": {"type": "array", "items": {"type": "string"}},
                "lifestyle_advice": {"type": "array", "items": {"type": "string"}},
                "cautions": {"type": "array", "items": {"type": "string"}},
                "disclaimer": {"type": "string"}
            },
            "required": ["patient_summary", "syndrome_analysis"]
        }
    }
}

def _get_agent_response_format(agent_name: str) -> Optional[Dict[str, Any]]:
    """根据Agent名称获取对应的JSON schema"""
    schemas = {
        "IntakeAgent": _INTAKE_JSON_SCHEMA,
        "InquiryAgent": _INQUIRY_JSON_SCHEMA,
        "SyndromeAgent": _SYNDROME_JSON_SCHEMA,
        "RecommendationAgent": _RECOMMENDATION_JSON_SCHEMA,
        "ReportAgent": _REPORT_JSON_SCHEMA,
    }
    return schemas.get(agent_name)


def _get_fallback_json(agent_name: str) -> Dict[str, Any]:
    """获取降级JSON响应"""
    fallbacks = {
        "IntakeAgent": {
            "chief_complaint": "",
            "symptoms": [],
            "age_group": None,
            "gender": None,
            "is_pregnant": False,
            "is_minor": False,
            "medical_history": [],
            "current_medications": [],
            "needs_clarification": []
        },
        "InquiryAgent": {
            "questions": ["请问您还有其他不适症状吗？"],
            "is_sufficient": False,
            "new_symptoms": [],
            "answered_dimensions": [],
            "inquiry_answers": {}
        },
        "SyndromeAgent": {
            "syndrome_candidates": [],
            "primary_syndrome": None,
            "constitution_inference": None,
            "insufficient_info": ["症状信息不足，无法准确辨证"],
            "evidence_summary": "降级模式：信息不足"
        },
        "RecommendationAgent": {
            "recommendations": [],
            "primary_syndrome": "其他证型",
            "overall_risk_level": "low",
            "should_see_doctor": False,
            "follow_up_questions": []
        },
        "ReportAgent": {
            "patient_summary": "问诊信息不足",
            "chief_complaint": "",
            "syndrome_analysis": {
                "primary_syndrome": "其他证型",
                "confidence": 0.5,
                "supporting_symptoms": [],
                "analysis": "降级模式：信息不足"
            },
            "recommendations": ["建议提供更多症状描述，或前往医疗机构就诊"],
            "lifestyle_advice": [],
            "cautions": [],
            "disclaimer": "本报告仅供参考，不构成医疗诊断"
        }
    }
    return fallbacks.get(agent_name, {})


def _normalize_lmstudio_base_url(base_url: str) -> str:
    raw = (base_url or "").strip() or "http://localhost:1234/v1"
    parsed = urlparse(raw)
    path = (parsed.path or "").rstrip("/")
    if path.endswith("/api/v1"):
        path = path[:-len("/api/v1")] + "/v1"
    elif path in {"", "/"}:
        path = "/v1"
    return urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment))


# ---------------------------------------------------------------------------
# 安全系统提示词注入
# ---------------------------------------------------------------------------

_SAFETY_SYSTEM_SUFFIX = """
【安全约束 - 必须严格遵守】
1. 本系统的输出定位为"健康建议与中医辨证参考"，严禁输出任何医疗诊断结论。
2. 禁止输出明确的处方药物剂量（可提及药物名称，但须注明"请在执业中医师指导下使用"）。
3. 若检测到高风险症状（如胸痛、呼吸困难、便血、意识障碍等），必须立即建议就医，不得给出诊疗建议。
"""


def build_system_prompt(base_prompt: str, extra_constraints: str = "") -> str:
    """构建包含安全约束的系统提示词"""
    if LIGHTWEIGHT_MODE:
        return f"{base_prompt}\n{extra_constraints}".strip()
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
            step_note=f"正在调用：{self.agent_name}",
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
        默认降级策略：根据错误类型给出不同提示。
        子类可覆盖提供更具体的降级内容。
        """
        logger.warning("[%s] executing fallback strategy", self.agent_name)
        new_state = state.model_copy(deep=True)
        
        # 区分错误类型，给出不同的降级提示
        error_type = self._classify_error_type()
        
        if error_type == ErrorType.TECHNICAL:
            # 技术错误：提示用户稍后重试，不中断问诊
            message = (
                f"[系统提示] {self.agent_name} 遇到技术问题，正在尝试恢复。"
                "请稍后重试，或继续描述您的症状。"
            )
        elif error_type == ErrorType.MEDICAL:
            # 医学相关错误：保守建议，但不强制就医
            message = (
                f"[系统提示] 当前分析遇到困难，可能需要更多信息。"
                "请补充更详细的症状描述，或前往医疗机构就诊。"
            )
        else:
            # 未知错误：给出通用提示
            message = (
                f"[系统提示] {self.agent_name} 处理遇到问题。"
                "请尝试重新描述您的症状，或前往医疗机构就诊。"
            )
        
        new_state.add_message("assistant", message)
        return new_state
    
    def _classify_error_type(self) -> ErrorType:
        """根据Agent类型和错误上下文分类错误类型"""
        # 可以根据last_error或其他上下文来判断
        # 默认返回技术错误
        return ErrorType.TECHNICAL

    # ------------------------------------------------------------------
    # LLM 调用辅助
    # ------------------------------------------------------------------

    def _call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2048,
        timeout: int = 60,  # 默认60秒超时
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
            return self._call_via_provider_manager(messages, temperature, max_tokens, timeout=timeout, **kwargs)
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
        """通过模型管理配置调用 LLM（支持按 Agent 绑定模型）。"""
        from django.conf import settings
        from apps.model_provider.models import AgentModelConfig, ModelConfig
        from apps.model_provider.provider_manager import global_provider_manager

        model_instance = None

        # 1) 优先读取 Agent 绑定模型
        try:
            agent_binding = (
                AgentModelConfig.objects.select_related("model")
                .filter(agent_name=self.agent_name, is_delete=False)
                .first()
            )
            if agent_binding and agent_binding.model and agent_binding.model.is_active and not agent_binding.model.is_delete:
                model_instance = agent_binding.model
        except Exception as exc:
            logger.warning("[%s] read AgentModelConfig failed: %s", self.agent_name, exc)

        # 2) 未绑定时回退到任意激活模型
        if model_instance is None:
            model_instance = (
                ModelConfig.objects
                .filter(is_delete=False, is_active=True, model_type="LLM")
                .order_by("create_time")
                .first()
            )

        if model_instance is not None:
            provider = global_provider_manager.get_provider(model_instance.provider)
            if provider:
                credential = model_instance.credential or {}
                model_params = model_instance.params or {}

                # 关键认证信息前置校验，避免进入 fallback 对话
                api_key = credential.get("api_key")
                no_key_providers = {"ollama", "vllm", "xorbits", "lmstudio"}
                if model_instance.provider not in no_key_providers and (not api_key or str(api_key).strip() == ""):
                    raise RuntimeError(
                        f"模型 {model_instance.name} 未配置 API Key（provider={model_instance.provider}）"
                    )

                configured_max_tokens = model_params.get("max_tokens")
                if isinstance(configured_max_tokens, (int, float)) and configured_max_tokens > 0:
                    final_max_tokens = min(max_tokens, int(configured_max_tokens))
                else:
                    final_max_tokens = max_tokens

                # 本地推理服务按 agent 收敛输出长度，避免 token 膨胀
                if model_instance.provider in {"lmstudio", "ollama", "vllm", "xorbits"}:
                    local_caps = {
                        "IntakeAgent": 1024,  # 增加到1024，确保JSON完整
                        "InquiryAgent": 1024,
                        "SyndromeAgent": 1024,
                        "RecommendationAgent": 2048,  # 增加到2048，确保建议完整
                        "ReportAgent": 2048,
                    }
                    min_required = {
                        "IntakeAgent": 512,
                        "InquiryAgent": 512,
                        "SyndromeAgent": 768,
                        "RecommendationAgent": 1024,
                        "ReportAgent": 1536,
                    }
                    final_max_tokens = max(final_max_tokens, min_required.get(self.agent_name, 512))
                    final_max_tokens = min(final_max_tokens, local_caps.get(self.agent_name, 512))

                model_credential = {
                    **credential,
                    "model": credential.get("model") or model_instance.model_name,
                    "temperature": temperature,
                    "max_tokens": final_max_tokens,
                    "timeout": model_params.get("timeout", 60),
                }

                # LM Studio 直连调用：避免 ChatOpenAI 丢失 reasoning_content 导致 content 为空
                if model_instance.provider == "lmstudio":
                    from openai import OpenAI  # type: ignore

                    base_url = _normalize_lmstudio_base_url(str(model_credential.get("base_url") or "http://localhost:1234/v1"))
                    api_key = model_credential.get("api_key") or "lm-studio"
                    model_name = str(model_credential.get("model") or model_instance.model_name)
                    client = OpenAI(api_key=api_key, base_url=base_url, timeout=model_credential.get("timeout", 60))
                    
                    # 获取Agent的JSON schema
                    response_format = _get_agent_response_format(self.agent_name)
                    
                    request_payload: Dict[str, Any] = {
                        "model": model_name,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": final_max_tokens,
                        "stream": False,
                    }
                    
                    # 如果有JSON schema，添加到请求中
                    if response_format:
                        request_payload["response_format"] = response_format
                        logger.debug(f"[{self.agent_name}] Using structured output with schema")

                    completion = client.chat.completions.create(**request_payload)

                    payload = completion.model_dump() if hasattr(completion, "model_dump") else {}
                    
                    # 调试：打印完整的payload结构
                    logger.debug(f"[{self.agent_name}] LM Studio payload keys: {list(payload.keys())}")
                    if payload.get("choices"):
                        choice0 = payload["choices"][0]
                        logger.debug(f"[{self.agent_name}] Choice0 keys: {list(choice0.keys())}")
                        message0 = choice0.get("message") or {}
                        logger.debug(f"[{self.agent_name}] Message0 keys: {list(message0.keys())}")
                        logger.debug(f"[{self.agent_name}] Message0 content: {repr(message0.get('content'))}")
                        logger.debug(f"[{self.agent_name}] Message0 reasoning_content: {repr(message0.get('reasoning_content', '')[:200])}")
                        for key, value in message0.items():
                            if value:
                                logger.debug(f"[{self.agent_name}] Message0[{key}] length: {len(str(value))}, preview: {str(value)[:100]}")
                            else:
                                logger.debug(f"[{self.agent_name}] Message0[{key}] is empty/None")
                    
                    choice0 = (payload.get("choices") or [{}])[0]
                    message0 = choice0.get("message") or {}
                    
                    # 优先使用 content 字段（实际响应内容）
                    # reasoning_content 是思考过程，不用于最终输出
                    content_value = message0.get("content")
                    logger.debug(f"[{self.agent_name}] Content value: {repr(content_value)}")
                    text = content_value or ""
                    
                    # 如果 content 为空或太短，尝试其他字段（兼容性）
                    # 注意：content可能是空字符串，需要检查长度
                    if not text or len(text.strip()) < 10:
                        logger.debug(f"[{self.agent_name}] Content is empty or too short, trying reasoning_content")
                        reasoning_content = message0.get("reasoning_content") or ""
                        
                        # 尝试从reasoning_content中提取JSON
                        if reasoning_content:
                            import re
                            # 查找```json代码块
                            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', reasoning_content, re.IGNORECASE)
                            if json_match:
                                text = json_match.group(1)
                                logger.debug(f"[{self.agent_name}] Extracted JSON from reasoning_content code block: {text[:200]}")
                            else:
                                # 尝试提取{}包裹的JSON对象
                                # 使用平衡括号匹配来提取完整的JSON对象
                                json_objects = []
                                stack = []
                                start_idx = None
                                for i, char in enumerate(reasoning_content):
                                    if char == '{':
                                        if not stack:
                                            start_idx = i
                                        stack.append(char)
                                    elif char == '}':
                                        if stack:
                                            stack.pop()
                                            if not stack and start_idx is not None:
                                                json_obj = reasoning_content[start_idx:i+1]
                                                json_objects.append(json_obj)
                                                start_idx = None
                                
                                if json_objects:
                                    # 使用最后一个JSON对象（通常是最完整的）
                                    text = json_objects[-1]
                                    logger.debug(f"[{self.agent_name}] Extracted JSON object from reasoning_content: {text[:200]}")
                                else:
                                    logger.warning(f"[{self.agent_name}] No JSON found in reasoning_content, using full reasoning_content as fallback")
                                    # 使用整个reasoning_content作为降级方案
                                    text = reasoning_content
                        else:
                            text = message0.get("reasoning") or ""
                    
                    # 调试日志
                    logger.debug(f"[{self.agent_name}] LM Studio raw response length: {len(str(text))}")
                    logger.debug(f"[{self.agent_name}] LM Studio raw response (first 500 chars): {str(text)[:500]}")
                    
                    # 检查是否使用了reasoning_content
                    if text and text.startswith("Thinking Process:"):
                        logger.warning(f"[{self.agent_name}] Using reasoning_content instead of content!")
                        # 尝试从content字段重新提取
                        content_value = message0.get("content")
                        if content_value and len(content_value.strip()) > 10:
                            text = content_value
                            logger.debug(f"[{self.agent_name}] Re-extracted content: {text[:200]}")
                        else:
                            logger.warning(f"[{self.agent_name}] Content field is empty or too short: '{content_value}'")
                    
                    if not str(text or "").strip():
                        raise RuntimeError("LM Studio 返回空响应（content/reasoning_content均为空）")

                    # 对结构化 agent 强制提取 JSON，避免把思维链原样传回上层
                    structured_agents = {
                        "IntakeAgent",
                        "InquiryAgent",
                        "SyndromeAgent",
                        "RecommendationAgent",
                        "ReportAgent",
                    }
                    if self.agent_name in structured_agents:
                        parsed = _extract_last_json_obj(str(text))
                        if parsed is None:
                            logger.error(f"[{self.agent_name}] Failed to extract JSON from response: {str(text)[:200]}")
                            # 如果没有找到JSON，尝试使用整个响应作为降级方案
                            # 但是只返回简化的JSON，而不是完整的响应
                            logger.warning(f"[{self.agent_name}] No JSON found, using simplified fallback")
                            # 创建一个简化的JSON响应
                            fallback_json = {
                                "chief_complaint": "",
                                "symptoms": [],
                                "age_group": None,
                                "gender": None,
                                "is_pregnant": False,
                                "is_minor": False,
                                "medical_history": [],
                                "current_medications": [],
                                "needs_clarification": []
                            }
                            return json.dumps(fallback_json, ensure_ascii=False)
                        logger.debug(f"[{self.agent_name}] Successfully extracted JSON with keys: {list(parsed.keys())}")
                        return json.dumps(parsed, ensure_ascii=False)

                    return _sanitize_reasoning_noise(str(text))

                local_kwargs: Dict[str, Any] = {}
                if model_instance.provider in {"lmstudio", "ollama", "vllm", "xorbits"}:
                    local_kwargs = {
                        "streaming": False,
                        **_build_local_reasoning_flags(),
                    }
                model = _resolve_model_runtime(
                    provider,
                    "LLM",
                    model_instance.model_name,
                    model_credential,
                    **local_kwargs,
                )
                if model is None or not hasattr(model, "invoke"):
                    raise RuntimeError(
                        f"模型实例不可用（provider={model_instance.provider}, model={model_instance.model_name}）"
                    )

                # 优先传消息数组，不支持时回退为拼接文本
                invoke_messages = messages
                if model_instance.provider in {"lmstudio", "ollama", "vllm", "xorbits"}:
                    invoke_messages = _trim_context_for_local_models(messages, keep_turns=5)

                try:
                    response = model.invoke(  # type: ignore[arg-type]
                        invoke_messages,
                        temperature=temperature,
                        max_tokens=final_max_tokens,
                    )
                except Exception:
                    prompt_text = "\n".join(
                        f"{m.get('role', 'user')}: {m.get('content', '')}" for m in invoke_messages
                    )
                    response = model.invoke(
                        prompt_text,
                        temperature=temperature,
                        max_tokens=final_max_tokens,
                    )

                response_text = _extract_text_from_model_response(response)
                return _sanitize_reasoning_noise(response_text)

        # 3) 最后回退到环境变量 OpenAI 兼容配置
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
        也支持 Qwen 模型的 reasoning_content 字段。
        """
        text = text.strip()
        
        # 检查是否是 Qwen 模型的 reasoning_content 格式
        # 模型返回格式: {"reasoning_content": "{\"questions\": ...}", ...}
        try:
            outer = json.loads(text)
            if isinstance(outer, dict):
                # 检查是否包含 reasoning_content 字段
                reasoning = outer.get("reasoning_content", "")
                if reasoning:
                    # 解析内部的 JSON
                    inner = json.loads(reasoning)
                    if inner:
                        logger.info("[_parse_json_output] 从 reasoning_content 解析成功")
                        return inner
                # 检查是否包含 content 字段
                content = outer.get("content", "")
                if content:
                    return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # 去除代码块标记
        if text.startswith("```"):
            lines = text.split("\n")
            # 去掉首尾的 ```json / ``` 行
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            parsed = _extract_last_json_obj(text)
            if parsed is not None:
                return parsed
        logger.warning("Failed to parse JSON from LLM output: %s", text[:200])
        return {}
