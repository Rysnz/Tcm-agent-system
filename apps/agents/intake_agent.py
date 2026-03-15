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
  "needs_clarification": ["还需要进一步澄清的问题列表，无则为空数组"]
}

只输出 JSON，不要包含其他文字。"""
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

        # 调用 LLM 提取结构化信息
        messages = [
            {"role": "system", "content": _INTAKE_SYSTEM_PROMPT},
            {"role": "user", "content": f"患者描述：{user_message}"},
        ]
        raw_output = self._call_llm(messages, temperature=0.1, max_tokens=1024)
        extracted = self._parse_json_output(raw_output)

        # 更新会话状态
        new_state = self._update_state_from_extraction(new_state, extracted)

        # 推进阶段
        new_state.current_stage = ConsultStage.INQUIRY

        return new_state

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

        # 主诉
        if data.get("chief_complaint"):
            state.chief_complaint = data["chief_complaint"]

        # 症状列表
        raw_symptoms: List[Dict] = data.get("symptoms", [])
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

        # 患者信息
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

        # 待澄清问题
        if data.get("needs_clarification"):
            state.pending_questions.extend(data["needs_clarification"])

        return state
