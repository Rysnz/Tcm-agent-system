"""
RecommendationAgent —— 调理建议智能体。

职责：
1. 基于辨证结果和体质类型，生成个性化调理建议。
2. 建议类型：饮食宜忌、作息调节、运动强度、情志调节、穴位保健、代茶饮。
3. 所有建议必须：
   - 可追溯到证型 + 体质 + RAG 依据。
   - 不包含明确处方剂量（由 SafetyGuardAgent 最终拦截）。
   - 对特殊人群（孕妇/未成年人）给出保守建议。
4. 支持个性化养生计划生成（基于九种体质）。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from apps.agents.base_agent import BaseAgent, build_system_prompt
from apps.agents.session_state import (
    ConsultStage,
    ConstitutionType,
    RecommendationItem,
    SessionState,
)

logger = logging.getLogger("apps.agents")

_RECOMMENDATION_SYSTEM_PROMPT = build_system_prompt(
    """你是一名经验丰富的中医调理建议专家。请根据患者的辨证结果和体质特点，
生成个性化的调理建议。

输出格式（严格 JSON）：
{
  "recommendations": [
    {
      "category": "类别（饮食宜忌/作息调节/运动建议/情志调节/穴位保健/代茶饮）",
      "content": "具体建议内容",
      "rationale": "依据（与证型/体质的关联说明）",
      "caution": "注意事项（可为null）"
    }
  ],
  "wellness_plan_summary": "一周养生计划摘要（3~5句话）",
  "key_points": ["核心注意事项1", "核心注意事项2"]
}

重要规则：
1. 禁止输出明确的处方药物剂量，可提及药物名称但须注明"遵医嘱"。
2. 代茶饮只推荐日常保健性质的（如枸杞菊花茶），不推荐处方级药茶。
3. 对妊娠期妇女：只给饮食和作息建议，禁止推荐穴位针灸和药物。
4. 对未成年人：建议更保守，优先建议就医。
5. 如果辨证不明确（证型置信度 < 0.4），给出通用养生建议而非针对性建议。
6. 每类建议至少1条，建议总数不超过8条。
7. 只输出 JSON，不要包含其他文字。"""
)

# 九种体质通用养生建议（降级时使用）
CONSTITUTION_WELLNESS_BASE: Dict[str, Dict[str, str]] = {
    "平和质": {
        "饮食宜忌": "饮食均衡，不偏食，五谷杂粮为主，适量肉类蔬果。",
        "运动建议": "适当运动，每日30分钟中等强度活动，如散步、太极拳。",
        "作息调节": "规律作息，子时（23:00）前入睡，保证7~8小时睡眠。",
    },
    "气虚质": {
        "饮食宜忌": "多食益气健脾食物：山药、红枣、南瓜、鸡肉。避免生冷、肥腻。",
        "运动建议": "以柔和运动为主，如散步、八段锦，避免大量出汗的剧烈运动。",
        "代茶饮": "黄芪红枣茶：黄芪10g、红枣5枚，代茶饮（遵医嘱）。",
    },
    "阳虚质": {
        "饮食宜忌": "多食温阳食物：生姜、韭菜、羊肉、核桃。忌生冷、冰镇食物。",
        "运动建议": "适当运动以温阳，避免在寒冷环境中运动，注意保暖。",
        "情志调节": "保持乐观积极，避免悲忧过度，多晒太阳。",
    },
    "阴虚质": {
        "饮食宜忌": "多食养阴食物：百合、银耳、梨、枸杞、鸭肉。忌辛辣燥热。",
        "作息调节": "避免熬夜，午休30分钟有益养阴，保证充足睡眠。",
        "代茶饮": "百合枸杞茶：百合6g、枸杞10g，代茶饮（遵医嘱）。",
    },
    "痰湿质": {
        "饮食宜忌": "少食甜腻、油炸食物，多食健脾化湿食物：薏苡仁、扁豆、冬瓜。",
        "运动建议": "加强有氧运动，如快走、游泳，促进水湿代谢，每日不少于45分钟。",
        "作息调节": "避免久坐，饭后适当活动，不宜在潮湿环境中居住。",
    },
    "湿热质": {
        "饮食宜忌": "清淡饮食，多食清热利湿食物：绿豆、苦瓜、芹菜。忌酒、辛辣、油腻。",
        "运动建议": "适量有氧运动，避免在高温潮湿环境中锻炼。",
        "代茶饮": "荷叶绿豆茶：荷叶6g、绿豆15g，代茶饮（遵医嘱）。",
    },
    "血瘀质": {
        "饮食宜忌": "多食活血化瘀食物：山楂、玫瑰花、黑木耳、三七（遵医嘱）。忌冷饮。",
        "运动建议": "坚持有氧运动，如慢跑、骑行，促进血液循环，避免久坐。",
        "情志调节": "保持心情舒畅，避免郁闷，可通过书法、音乐等舒缓情绪。",
    },
    "气郁质": {
        "饮食宜忌": "多食疏肝理气食物：玫瑰花、佛手、柑橘。避免过食酸涩之物。",
        "情志调节": "积极参加社交活动，培养兴趣爱好，必要时进行心理疏导。",
        "代茶饮": "玫瑰花茶：玫瑰花5朵，代茶饮，舒肝解郁（遵医嘱）。",
    },
    "特禀质": {
        "饮食宜忌": "避免已知过敏原，饮食清淡，避免海鲜、花粉等易致敏食物。",
        "运动建议": "根据自身情况适当运动，避免在花粉高峰期户外运动。",
        "作息调节": "规律作息，增强免疫力，注意居住环境清洁，减少过敏原。",
    },
}


class RecommendationAgent(BaseAgent):
    """调理建议 Agent"""

    agent_name = "RecommendationAgent"
    stage = ConsultStage.RECOMMENDATION

    def _execute(self, state: SessionState, **kwargs) -> SessionState:
        new_state = state.model_copy(deep=True)

        # 如果是高风险状态，不生成建议
        if new_state.is_high_risk:
            new_state.current_stage = ConsultStage.SAFETY_CHECK
            return new_state

        # 构建 LLM 输入
        context_summary = new_state.to_context_summary()
        syndrome_info = self._format_syndrome_info(new_state)
        constitution = new_state.patient_profile.constitution

        # 特殊人群额外约束
        special_constraints = self._build_special_constraints(new_state)

        messages = [
            {"role": "system", "content": _RECOMMENDATION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"【患者信息】\n{context_summary}\n\n"
                    f"【辨证结果】\n{syndrome_info}\n\n"
                    f"【体质类型】{constitution}\n\n"
                    f"【特殊约束】{special_constraints}\n\n"
                    "请生成个性化调理建议，以 JSON 格式返回："
                ),
            },
        ]

        raw = self._call_llm(messages, temperature=0.3, max_tokens=2048)
        data = self._parse_json_output(raw)

        new_state = self._update_state(new_state, data)
        new_state.current_stage = ConsultStage.SAFETY_CHECK
        return new_state

    def _fallback(self, state: SessionState) -> SessionState:
        """降级：使用体质对应的通用养生建议"""
        new_state = state.model_copy(deep=True)
        constitution_value = new_state.patient_profile.constitution

        # 处理枚举值
        if hasattr(constitution_value, 'value'):
            constitution_str = constitution_value.value
        else:
            constitution_str = str(constitution_value)

        base_advice = CONSTITUTION_WELLNESS_BASE.get(
            constitution_str,
            CONSTITUTION_WELLNESS_BASE["平和质"],
        )
        recommendations: List[RecommendationItem] = []
        for category, content in base_advice.items():
            recommendations.append(
                RecommendationItem(
                    category=category,
                    content=content,
                    rationale=f"基于{constitution_str}体质的通用建议",
                )
            )

        new_state.recommendations = recommendations
        new_state.current_stage = ConsultStage.SAFETY_CHECK
        return new_state

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------

    def _format_syndrome_info(self, state: SessionState) -> str:
        if not state.syndrome_candidates:
            return "辨证结果未明确"
        lines: List[str] = []
        for cand in state.syndrome_candidates[:3]:
            lines.append(
                f"证型：{cand.name}（置信度：{cand.confidence:.0%}）"
                f"\n  支持症状：{', '.join(cand.supporting_symptoms[:5])}"
            )
        return "\n".join(lines)

    def _build_special_constraints(self, state: SessionState) -> str:
        constraints: List[str] = []
        if state.patient_profile.is_pregnant:
            constraints.append(
                "患者为妊娠期妇女，禁止推荐针灸穴位和任何内服药物，"
                "只给予饮食和作息建议，所有建议须非常保守。"
            )
        if state.patient_profile.is_minor:
            constraints.append(
                "患者为未成年人，建议保守，优先建议就医，"
                "不推荐任何药物或穴位。"
            )
        return "；".join(constraints) if constraints else "无特殊约束"

    def _update_state(self, state: SessionState, data: Dict[str, Any]) -> SessionState:
        if not data:
            return state

        recommendations: List[RecommendationItem] = []
        for item in data.get("recommendations", []):
            if item.get("content"):
                recommendations.append(
                    RecommendationItem(
                        category=item.get("category", "建议"),
                        content=item["content"],
                        rationale=item.get("rationale", ""),
                        caution=item.get("caution"),
                    )
                )
        state.recommendations = recommendations
        return state
