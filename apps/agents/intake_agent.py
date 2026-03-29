"""
IntakeAgent —— 接诊分诊智能体。

职责：
1. 从用户首条消息中提取主诉、年龄段、性别、病程信息。
2. 初步识别患者基本信息（是否特殊人群）。
3. 在 SafetyGuardAgent 快速预检后，决定是否继续问诊或立即转介。
4. 输出结构化 SymptomInfo 列表 + PatientProfile 更新。

输出写入 SessionState：
- chief_complaint
- patient_profile（部分字段）
- symptoms（初步列表）
- current_stage → ConsultStage.INQUIRY（通常）
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from apps.agents.base_agent import BaseAgent, build_system_prompt
from apps.agents.session_state import (
    ConsultStage,
    PatientProfile,
    SessionState,
    SymptomInfo,
)

logger = logging.getLogger("apps.agents")

_INTAKE_SYSTEM_PROMPT = build_system_prompt(
    """你是一名经验丰富的中医接诊助手。你的任务是从患者的描述中提取关键信息，
并以结构化 JSON 格式返回。

提取以下信息（能提取多少提取多少，无法确定的字段填 null）：
{
  "chief_complaint": "主诉（患者最主要的不适，一句话概括）",
  "symptoms": [
    {
      "name": "症状名称",
      "duration": "持续时间（如'3天'，无则填null）",
      "severity": "轻/中/重（无则填null）",
      "onset": "急/缓（无则填null）"
    }
  ],
  "age_group": "儿童/青年/中年/老年（无则填null）",
  "gender": "男/女（无则填null）",
  "is_pregnant": true/false,
  "is_minor": true/false,
  "medical_history": ["既往病史列表，无则为空数组"],
  "current_medications": ["正在使用的药物列表，无则为空数组"],
  "needs_clarification": ["需要进一步澄清的问题，用于追问。至少包含1-2个问题，如具体症状部位、性质、伴随症状等"]
}

【重要】needs_clarification 必须包含至少1个问题，用于后续追问。即使信息看似完整，也请列出需要进一步确认的问题。

只输出 JSON，不要包含其他文字。
严禁输出 reasoning、思考过程、解释说明。"""
)


class IntakeAgent(BaseAgent):
    """接诊分诊 Agent"""

    agent_name = "IntakeAgent"
    stage = ConsultStage.INTAKE

    def _execute(self, state: SessionState, **kwargs) -> SessionState:
        new_state = state.model_copy(deep=True)

        # 获取最新的用户消息
        user_message = self._get_latest_user_message(new_state)
        if not user_message:
            new_state.add_message(
                "assistant",
                "您好！我是中医智能问诊助手。请描述您目前的主要不适或症状，"
                "例如：持续时间、发作方式、伴随症状等。",
            )
            return new_state

        # 对简单问候走规则分流，避免浪费一次大模型调用
        if self._is_greeting_only(user_message):
            new_state.pending_questions = [
                "请问您目前主要有哪些不适症状？",
                "大概持续多久了？",
            ]
            new_state.add_message(
                "assistant",
                "1. 请问您目前主要有哪些不适症状？\n"
                "2. 大概持续多久了？",
            )
            new_state.current_stage = ConsultStage.INQUIRY
            return new_state

        # 调用 LLM 提取结构化信息
        messages = [
            {"role": "system", "content": _INTAKE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"患者描述：{user_message}\n\n"
                    "请严格只返回JSON对象，不要输出任何思考过程或解释。"
                ),
            },
        ]
        raw_output = self._call_llm(messages, temperature=0.1, max_tokens=1024)
        extracted = self._parse_json_output(raw_output)
        if not extracted:
            raise ValueError("IntakeAgent 未获取到可解析的结构化输出")

        # 更新会话状态
        new_state = self._update_state_from_extraction(new_state, extracted)

        # 推进阶段
        new_state.current_stage = ConsultStage.INQUIRY

        return new_state

    @staticmethod
    def _is_greeting_only(text: str) -> bool:
        if not text:
            return False
        cleaned = re.sub(r"\s+", "", text.lower())
        return cleaned in {
            "你好", "您好", "hi", "hello", "hey", "在吗", "有人吗", "嗨", "哈喽"
        }

    def _fallback(self, state: SessionState) -> SessionState:
        """降级：使用规则提取主诉"""
        new_state = state.model_copy(deep=True)
        user_message = self._get_latest_user_message(new_state)
        if user_message:
            new_state.chief_complaint = user_message[:200]
        new_state.add_message(
            "assistant",
            "感谢您的描述。为了更好地为您服务，"
            "请问您目前主要的不适症状是什么？持续多长时间了？",
        )
        new_state.current_stage = ConsultStage.INQUIRY
        return new_state

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _get_latest_user_message(self, state: SessionState) -> str:
        for msg in reversed(state.messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return ""

    def _update_state_from_extraction(
        self, state: SessionState, data: Dict[str, Any]
    ) -> SessionState:
        if not data:
            return state

        # 主诉 - 支持多种格式
        if data.get("chief_complaint"):
            state.chief_complaint = data["chief_complaint"]
        elif data.get("诊断分析", {}).get("主要症状"):
            # LM Studio格式：从"诊断分析"中提取主诉
            symptoms = data["诊断分析"]["主要症状"]
            state.chief_complaint = "、".join(symptoms) if symptoms else ""
        elif data.get("主要症状"):
            # 另一种可能的格式
            symptoms = data["主要症状"]
            state.chief_complaint = "、".join(symptoms) if symptoms else ""
        
        # 如果LLM没有返回chief_complaint，从用户消息中提取
        if not state.chief_complaint:
            user_messages = [m for m in state.messages if m.get("role") == "user"]
            if user_messages:
                # 使用最后一条用户消息作为主诉，但要过滤掉无意义的输入
                last_user_msg = user_messages[-1].get("content", "")
                # 过滤掉问候语和过短的消息（少于3个字符可能是误输入）
                invalid_inputs = ["你好", "您好", "hi", "hello", "嗯", "好的", "ok"]
                if last_user_msg and len(last_user_msg) >= 3 and last_user_msg.lower() not in invalid_inputs:
                    state.chief_complaint = last_user_msg[:500]

        # 症状列表 - 支持多种格式
        raw_symptoms: List[Dict] = []
        if data.get("symptoms"):
            raw_symptoms = data["symptoms"]
        elif data.get("诊断分析", {}).get("主要症状"):
            # LM Studio格式：从"诊断分析"中提取症状
            for sym_name in data["诊断分析"]["主要症状"]:
                raw_symptoms.append({"name": sym_name})
        elif data.get("主要症状"):
            # 另一种可能的格式
            for sym_name in data["主要症状"]:
                raw_symptoms.append({"name": sym_name})
        
        for sym in raw_symptoms:
            if sym.get("name"):
                state.symptoms.append(
                    SymptomInfo(
                        name=sym["name"],
                        duration=sym.get("duration"),
                        severity=sym.get("severity"),
                        onset=sym.get("onset"),
                    )
                )

        # 患者信息 - 支持多种格式
        profile = state.patient_profile
        if data.get("age_group"):
            profile.age_group = data["age_group"]
        if data.get("gender"):
            profile.gender = data["gender"]
        if data.get("is_pregnant") is True:
            profile.is_pregnant = True
        if data.get("is_minor") is True:
            profile.is_minor = True
        if data.get("medical_history"):
            profile.medical_history.extend(data["medical_history"])
        if data.get("current_medications"):
            profile.current_medications.extend(data["current_medications"])
        state.patient_profile = profile

        # 待澄清问题 - 支持多种格式
        if data.get("needs_clarification"):
            state.pending_questions.extend(data["needs_clarification"])
        elif data.get("注意事项", {}).get("就医提示"):
            # LM Studio格式：从"注意事项"中提取就医提示
            state.pending_questions.append(data["注意事项"]["就医提示"])

        # 添加接诊完成消息
        chief = state.chief_complaint or "您的症状"
        assistant_msg = f"已记录您的主诉：{chief}。接下来我将通过系统化的问诊为您进行中医辨证分析。"
        
        # 如果有待追问问题，添加到助手消息中
        if state.pending_questions:
            questions_text = "\n".join(
                f"{i+1}. {q}" for i, q in enumerate(state.pending_questions[:2])
            )
            assistant_msg += "\n\n" + questions_text
        
        state.add_message("assistant", assistant_msg)

        return state
