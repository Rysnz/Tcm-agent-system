"""
ObservationAgent —— 望诊融合智能体。

职责：
1. 解析用户上传的舌象/面色图片（调用视觉模型提取特征）。
2. 将视觉特征（舌色、苔色、苔厚薄、苔质、舌形、面色）结构化写入 ObservationData。
3. 若无图片，则通过对话询问舌象/面色描述。
4. 将图像特征作为下游辨证的额外证据。

多模态 MVP 策略：
- 优先使用视觉 LLM（如 GPT-4V / Qwen-VL）分析图片。
- 若视觉模型不可用，退回到文本追问模式（询问舌色等）。
- 图像分析结果只作为"辅助特征"，不单独给出诊断结论。
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from apps.agents.base_agent import BaseAgent, build_system_prompt
from apps.agents.session_state import (
    ConsultStage,
    ObservationData,
    SessionState,
)

logger = logging.getLogger("apps.agents")

_TONGUE_ANALYSIS_SYSTEM_PROMPT = build_system_prompt(
    """你是一名中医舌诊专家。请根据提供的舌象图片，提取以下特征，
并以结构化 JSON 格式返回（不确定的字段填 null）：

{
  "tongue_color": "舌色：淡白/淡红/红/绛/紫（不确定填null）",
  "tongue_coating": "苔色：白/黄/灰/黑（不确定填null）",
  "coating_thickness": "苔厚薄：薄/厚（不确定填null）",
  "coating_texture": "苔质：润/燥/腻/剥落（不确定填null）",
  "tongue_shape": "舌形：正常/胖大/瘦薄/裂纹/齿痕（不确定填null）",
  "image_features": ["提取到的视觉特征描述列表"],
  "analysis_notes": "分析说明（图像质量评估、特殊发现等）"
}

重要：
- 本分析仅供中医辅助参考，不构成诊断结论。
- 如图像质量较差或特征不明显，请在 analysis_notes 中注明。
- 只输出 JSON，不要包含其他文字。"""
)

_OBSERVATION_TEXT_SYSTEM_PROMPT = build_system_prompt(
    """你是一名中医望诊助手。根据患者的文字描述，提取望诊相关信息，
并以 JSON 格式返回：

{
  "tongue_color": "舌色（淡白/淡红/红/绛/紫，不确定填null）",
  "tongue_coating": "苔色（白/黄/灰/黑，不确定填null）",
  "coating_thickness": "苔厚薄（薄/厚，不确定填null）",
  "coating_texture": "苔质（润/燥/腻/剥落，不确定填null）",
  "tongue_shape": "舌形（正常/胖大/瘦薄/裂纹/齿痕，不确定填null）",
  "face_color": "面色（红润/苍白/萎黄/晦暗/青紫，不确定填null）",
  "image_features": ["提取到的特征列表"],
  "needs_image": true/false （是否建议上传图片以便更准确分析）
}

只输出 JSON，不要包含其他文字。"""
)


class ObservationAgent(BaseAgent):
    """望诊融合 Agent（支持图像分析 + 文本回退）"""

    agent_name = "ObservationAgent"
    stage = ConsultStage.OBSERVATION

    def _execute(self, state: SessionState, **kwargs) -> SessionState:
        new_state = state.model_copy(deep=True)

        image_path: Optional[str] = kwargs.get("image_path")
        image_bytes: Optional[bytes] = kwargs.get("image_bytes")

        if image_path or image_bytes:
            # 图像分析模式
            observation = self._analyze_image(image_path, image_bytes)
        else:
            # 文本模式：从对话中提取望诊信息
            observation = self._extract_from_text(new_state)

        new_state.observation = observation
        new_state.current_stage = ConsultStage.SYNDROME
        return new_state

    def _fallback(self, state: SessionState) -> SessionState:
        """降级：跳过望诊，直接进入辨证"""
        new_state = state.model_copy(deep=True)
        new_state.current_stage = ConsultStage.SYNDROME
        new_state.add_message(
            "assistant",
            "图像分析暂时不可用，将根据症状描述进行辨证分析。"
        )
        return new_state

    # ------------------------------------------------------------------
    # 图像分析
    # ------------------------------------------------------------------

    def _analyze_image(
        self,
        image_path: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
    ) -> ObservationData:
        """调用视觉 LLM 分析舌象图片"""
        try:
            # 准备 base64 编码的图片
            if image_bytes:
                b64_image = base64.b64encode(image_bytes).decode("utf-8")
            elif image_path:
                with open(image_path, "rb") as f:
                    b64_image = base64.b64encode(f.read()).decode("utf-8")
            else:
                raise ValueError("No image provided")

            # 检测图片格式
            mime_type = "image/jpeg"
            if image_path:
                suffix = Path(image_path).suffix.lower()
                if suffix == ".png":
                    mime_type = "image/png"

            # 构建视觉 LLM 消息
            messages = [
                {"role": "system", "content": _TONGUE_ANALYSIS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64_image}",
                                "detail": "high",
                            },
                        },
                        {
                            "type": "text",
                            "text": "请分析这张舌象图片，提取望诊特征。",
                        },
                    ],
                },
            ]

            raw = self._call_llm(messages, temperature=0.1, max_tokens=1024)
            data = self._parse_json_output(raw)
            return self._build_observation_from_dict(data)

        except Exception as exc:
            logger.warning("Image analysis failed: %s", exc)
            # 返回空观察数据，不阻断流程
            return ObservationData(
                image_features=["图像分析失败，请通过文字描述舌象"],
            )

    # ------------------------------------------------------------------
    # 文本提取
    # ------------------------------------------------------------------

    def _extract_from_text(self, state: SessionState) -> ObservationData:
        """从对话文本中提取望诊信息"""
        # 收集用户消息中的望诊相关描述
        user_texts = [
            msg["content"]
            for msg in state.messages
            if msg.get("role") == "user"
        ]
        combined_text = "\n".join(user_texts[-5:])  # 只取最近 5 条

        if not combined_text.strip():
            return ObservationData()

        messages = [
            {"role": "system", "content": _OBSERVATION_TEXT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"请从以下用户描述中提取望诊信息：\n{combined_text}"
                ),
            },
        ]
        raw = self._call_llm(messages, temperature=0.1, max_tokens=512)
        data = self._parse_json_output(raw)

        # 如果建议上传图片
        if data.get("needs_image") and not state.has_image:
            state.pending_questions.append(
                "为了更准确地进行望诊分析，您可以上传舌头照片（舌象图）。"
                "如不方便，请描述您舌头的颜色和舌苔情况。"
            )

        return self._build_observation_from_dict(data)

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------

    def _build_observation_from_dict(self, data: Dict[str, Any]) -> ObservationData:
        return ObservationData(
            tongue_color=data.get("tongue_color"),
            tongue_coating=data.get("tongue_coating"),
            coating_thickness=data.get("coating_thickness"),
            coating_texture=data.get("coating_texture"),
            tongue_shape=data.get("tongue_shape"),
            face_color=data.get("face_color"),
            image_features=data.get("image_features", []),
            image_analysis_raw=data,
        )
