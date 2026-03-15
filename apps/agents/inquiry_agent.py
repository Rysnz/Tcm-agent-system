"""
InquiryAgent —— 问诊追问智能体（十问策略）。

中医十问歌（明·张景岳）：
一问寒热二问汗，三问头身四问便，
五问饮食六问胸，七聋八渴俱当辨，
九问旧病十问因，再兼服药参机变。

职责：
1. 根据当前已知症状，动态选择最相关的追问维度。
2. 生成 1~3 个追问问题（避免一次问太多让用户疲惫）。
3. 解析用户回答并填充 inquiry_answers。
4. 判断信息是否充足 → 推进到 SyndromeAgent。

状态转换：
- 信息不足 → 继续 INQUIRY（设置 pending_questions）
- 信息充足 → 推进到 OBSERVATION 或 SYNDROME
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from apps.agents.base_agent import BaseAgent, build_system_prompt
from apps.agents.session_state import (
    ConsultStage,
    SessionState,
    SymptomInfo,
)

logger = logging.getLogger("apps.agents")

# 十问框架
TEN_QUESTIONS = {
    "寒热": "请问您有没有感觉怕冷或发热？体温多少？",
    "汗液": "请问您有没有出汗异常？比如自汗、盗汗或无汗？",
    "头身": "请问您有没有头痛、头晕或身体某部位疼痛？",
    "大便": "请问您最近大便情况如何？次数、质地（干硬/稀溏）、颜色？",
    "小便": "请问您最近小便情况如何？颜色（深/浅）、次数、有无不适？",
    "饮食": "请问您饮食情况如何？食欲好不好？口中有无异味？",
    "胸腹": "请问您胸部或腹部有没有胀满、疼痛或不适感？",
    "耳目": "请问您近期有没有耳鸣、听力下降或视力变化？",
    "口渴": "请问您口渴吗？喜欢喝热饮还是冷饮？",
    "旧病": "请问您有什么慢性病史或者过敏史吗？",
}

_INQUIRY_SYSTEM_PROMPT = build_system_prompt(
    """你是一名专业的中医问诊助手，擅长通过"十问"策略系统地收集患者信息。

你的任务：
1. 根据已知症状和已有答案，判断哪些维度还需要追问。
2. 生成最多2个最相关的追问问题（简洁、口语化、一次不超过2问）。
3. 如果信息已经充足（已覆盖至少5个维度或症状明确），返回 is_sufficient=true。
4. 如果用户的回答包含新症状信息，提取出来。

以 JSON 格式返回：
{
  "questions": ["问题1（如无需追问则为空数组）"],
  "is_sufficient": true/false,
  "new_symptoms": [{"name": "新症状", "duration": null, "severity": null, "onset": null}],
  "answered_dimensions": ["已覆盖的十问维度，如：寒热、汗液"],
  "inquiry_answers": {"维度名": "答案摘要"}
}

只输出 JSON，不要包含其他文字。"""
)


class InquiryAgent(BaseAgent):
    """十问追问 Agent"""

    agent_name = "InquiryAgent"
    stage = ConsultStage.INQUIRY

    # 最少需要覆盖的维度数才能推进到辨证
    MIN_DIMENSIONS_REQUIRED = 4

    def _execute(self, state: SessionState, **kwargs) -> SessionState:
        new_state = state.model_copy(deep=True)

        # 如果已有待回答的问题，先解析用户的回答
        user_reply = self._get_latest_user_message(new_state)

        # 构建 LLM 输入
        context_summary = new_state.to_context_summary()
        already_answered = ", ".join(new_state.inquiry_answers.keys()) or "无"
        symptoms_str = ", ".join(s.name for s in new_state.symptoms) or "未明确"

        messages = [
            {"role": "system", "content": _INQUIRY_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"当前问诊上下文：\n{context_summary}\n\n"
                    f"已收集症状：{symptoms_str}\n"
                    f"已覆盖的十问维度：{already_answered}\n"
                    f"用户最新回答：{user_reply or '（首次进入问诊）'}\n\n"
                    "请判断下一步如何追问，并以 JSON 格式返回。"
                ),
            },
        ]

        raw = self._call_llm(messages, temperature=0.2, max_tokens=1024)
        data = self._parse_json_output(raw)

        new_state = self._update_state(new_state, data)
        return new_state

    def _fallback(self, state: SessionState) -> SessionState:
        """降级：使用预设问题"""
        new_state = state.model_copy(deep=True)
        # 找到尚未回答的第一个维度
        unanswered = [
            q for dim, q in TEN_QUESTIONS.items()
            if dim not in new_state.inquiry_answers
        ]
        if unanswered:
            question = unanswered[0]
            new_state.pending_questions = [question]
            new_state.add_message("assistant", question)
        else:
            new_state.current_stage = ConsultStage.SYNDROME
        return new_state

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _get_latest_user_message(self, state: SessionState) -> str:
        for msg in reversed(state.messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return ""

    def _update_state(self, state: SessionState, data: Dict[str, Any]) -> SessionState:
        if not data:
            return state

        # 更新新症状
        for sym in data.get("new_symptoms", []):
            if sym.get("name"):
                state.symptoms.append(
                    SymptomInfo(
                        name=sym["name"],
                        duration=sym.get("duration"),
                        severity=sym.get("severity"),
                        onset=sym.get("onset"),
                    )
                )

        # 更新十问答案
        for k, v in data.get("inquiry_answers", {}).items():
            state.inquiry_answers[k] = v

        # 设置待追问问题
        questions: List[str] = data.get("questions", [])
        state.pending_questions = questions

        # 判断是否信息充足
        is_sufficient = data.get("is_sufficient", False)
        answered_count = len(state.inquiry_answers)

        if is_sufficient or answered_count >= self.MIN_DIMENSIONS_REQUIRED:
            # 信息充足，推进
            if state.has_image:
                state.current_stage = ConsultStage.OBSERVATION
            else:
                state.current_stage = ConsultStage.SYNDROME
            state.pending_questions = []
        else:
            # 继续追问
            state.current_stage = ConsultStage.INQUIRY
            if questions:
                # 将追问问题合并为一条助手消息
                combined = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
                state.add_message("assistant", combined)

        return state
