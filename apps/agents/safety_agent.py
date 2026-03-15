"""
SafetyGuardAgent —— 安全审查智能体。

职责：
1. 检测高危关键词（胸痛、呼吸困难、便血、意识障碍等）→ 触发立即就医建议。
2. 识别特殊人群（未成年人、孕产妇）→ 应用保守策略。
3. 拦截不符合安全规范的建议内容（如明确处方剂量）。
4. 设置 SessionState.is_high_risk 标志，下游 Agent 必须遵从。

设计原则：
- 本 Agent 在 RecommendationAgent 之后、ReportAgent 之前运行。
- 亦可在 IntakeAgent 后立即运行（快速预检），以便早期中止。
"""
from __future__ import annotations

import re
from typing import List

from apps.agents.base_agent import BaseAgent, build_system_prompt
from apps.agents.session_state import (
    ConsultStage,
    RecommendationItem,
    RiskLevel,
    SafetyCheckResult,
    SessionState,
)

# ---------------------------------------------------------------------------
# 高危关键词库（可从数据库/配置文件扩展）
# ---------------------------------------------------------------------------

# 立即就医 - 生命体征威胁性症状
CRITICAL_KEYWORDS: List[str] = [
    # 心脑血管
    "胸痛", "胸闷痛", "心绞痛", "心肌梗死", "心跳骤停",
    "突发胸痛", "放射性胸痛", "剧烈胸痛",
    # 呼吸
    "呼吸困难", "呼吸衰竭", "喘不过气", "窒息", "气喘发作",
    # 神经
    "意识障碍", "昏迷", "昏厥", "失去意识", "突然晕倒",
    "抽搐", "癫痫发作", "半身不遂", "口眼歪斜",
    "言语不清", "突发失语", "肢体麻木无力",
    # 消化道出血
    "便血", "呕血", "黑便", "柏油样便", "大量出血",
    "呕吐鲜血", "吐血",
    # 外伤/急症
    "高烧不退", "体温超过39", "持续高热",
    "严重头痛", "雷击样头痛", "突然剧烈头痛",
    # 其他急症
    "急性腹痛", "剧烈腹痛", "刀割样疼痛",
    "大量脱水", "休克", "血压骤降",
]

# 高风险但非立即致命
HIGH_RISK_KEYWORDS: List[str] = [
    "持续发烧", "反复高热", "咳血", "血尿",
    "急性疼痛", "剧烈头痛", "持续头痛",
    "骨折", "外伤严重", "化脓", "感染扩散",
    "视力突然下降", "突然耳聋", "吞咽困难",
    "大量腹泻", "不明原因消瘦",
]

# 禁止输出的内容模式（正则）
FORBIDDEN_CONTENT_PATTERNS: List[str] = [
    r"\d+\s*g\s*[，,，。.]*\s*水煎服",          # 明确剂量 + 服用方式
    r"处方[:：]\s*[^\n]+\d+\s*[克g克]",          # 处方格式含剂量
    r"每日[一二三]\s*剂[，,]*[每次]\s*\d+",      # 明确服用频次剂量
]


class SafetyGuardAgent(BaseAgent):
    """
    安全审查 Agent。

    快速预检模式（quick_check=True）：
        仅做关键词匹配，不调用 LLM，适合在 IntakeAgent 后立即调用。

    完整模式（quick_check=False，默认）：
        调用 LLM 对建议文本进行语义级别的安全审查。
    """

    agent_name = "SafetyGuardAgent"
    stage = ConsultStage.SAFETY_CHECK

    def __init__(self, llm_caller=None, quick_check: bool = False):
        super().__init__(llm_caller)
        self.quick_check = quick_check

    # ------------------------------------------------------------------
    # 核心执行
    # ------------------------------------------------------------------

    def _execute(self, state: SessionState, **kwargs) -> SessionState:
        new_state = state.model_copy(deep=True)

        # 1. 收集所有要检查的文本
        texts_to_check = self._collect_texts(new_state)

        # 2. 关键词匹配检查
        critical_hits, high_risk_hits = self._keyword_scan(texts_to_check)

        # 3. 构建安全结果
        safety_result = SafetyCheckResult()

        if critical_hits:
            safety_result.risk_level = RiskLevel.CRITICAL
            safety_result.triggered_keywords = critical_hits
            safety_result.should_refer_immediately = True
            safety_result.safety_message = self._build_refer_message(critical_hits)
            new_state.mark_high_risk(safety_result.safety_message)

        elif high_risk_hits:
            safety_result.risk_level = RiskLevel.HIGH
            safety_result.triggered_keywords = high_risk_hits
            safety_result.safety_message = (
                "检测到高风险症状，建议尽快前往医院就诊，"
                "本系统的建议仅供参考。"
            )

        # 4. 特殊人群检查
        special_flags = self._check_special_population(new_state)
        safety_result.special_population_flags = special_flags

        # 5. 处方剂量拦截
        blocked = self._intercept_forbidden_content(new_state)
        if blocked:
            safety_result.blocked_content = blocked

        # 6. 完整模式：LLM 语义审查
        if not self.quick_check and new_state.recommendations:
            llm_note = self._llm_safety_review(new_state)
            if llm_note:
                safety_result.safety_message = (
                    (safety_result.safety_message or "") + "\n" + llm_note
                ).strip()

        new_state.safety_result = safety_result

        # 如果立即就医，清空可能误导患者的建议
        if safety_result.should_refer_immediately:
            new_state.recommendations = [
                RecommendationItem(
                    category="安全提示",
                    content=safety_result.safety_message or "请立即就医",
                    rationale="检测到高风险症状",
                )
            ]

        return new_state

    def _fallback(self, state: SessionState) -> SessionState:
        """安全审查失败时，标记为高风险（保守策略）"""
        new_state = state.model_copy(deep=True)
        new_state.mark_high_risk("安全审查未能完成，保守起见建议就医。")
        return new_state

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _collect_texts(self, state: SessionState) -> List[str]:
        """收集需要安全检查的所有文本"""
        texts: List[str] = [state.chief_complaint]
        texts.extend(s.name for s in state.symptoms)
        texts.extend(state.inquiry_answers.values())
        texts.extend(r.content for r in state.recommendations)
        texts.extend(m["content"] for m in state.messages if m.get("role") == "user")
        return [t for t in texts if t]

    def _keyword_scan(self, texts: List[str]) -> tuple[List[str], List[str]]:
        """关键词扫描，返回 (critical命中列表, high_risk命中列表)"""
        combined = " ".join(texts)
        critical_hits = [kw for kw in CRITICAL_KEYWORDS if kw in combined]
        high_risk_hits = [kw for kw in HIGH_RISK_KEYWORDS if kw in combined]
        return critical_hits, high_risk_hits

    def _check_special_population(self, state: SessionState) -> List[str]:
        """检查特殊人群标记"""
        flags: List[str] = []
        if state.patient_profile.is_pregnant:
            flags.append("妊娠期妇女")
        if state.patient_profile.is_minor:
            flags.append("未成年人")
        if state.patient_profile.age_group in ("老年",):
            flags.append("老年患者")
        return flags

    def _intercept_forbidden_content(self, state: SessionState) -> str:
        """拦截包含明确处方剂量的建议文本，返回被拦截的内容摘要"""
        intercepted: List[str] = []
        safe_recommendations: List[RecommendationItem] = []

        for item in state.recommendations:
            has_forbidden = any(
                re.search(pattern, item.content)
                for pattern in FORBIDDEN_CONTENT_PATTERNS
            )
            if has_forbidden:
                intercepted.append(f"[{item.category}] {item.content[:80]}")
                # 用正则去除剂量部分，保留药材名/方向等有效内容
                import re as _re
                # 移除具体剂量（如 "30g", "20克" 等）
                safe_content = _re.sub(
                    r'\d+\.?\d*\s*[gG克两钱][\s，,]?',
                    "",
                    item.content,
                )
                # 移除用药频率/服法等处方指令（如 "水煎服", "每日一剂", "日两次" 等）
                safe_content = _re.sub(
                    r'(水煎服|每日[一二三两1-3]剂|早晚分服|饭[前后]服|日[一二三两1-3]次|冲服)',
                    "",
                    safe_content,
                )
                safe_content = safe_content.strip().rstrip("，,、；;")
                if not safe_content:
                    safe_content = item.content[:30]  # 降级兜底
                safe_recommendations.append(
                    RecommendationItem(
                        category=item.category,
                        content=(
                            safe_content
                            + "（具体用药请在执业中医师指导下进行，本系统不提供处方剂量）"
                        ),
                        rationale=item.rationale,
                        caution="请勿自行配药，须遵医嘱。",
                    )
                )
            else:
                safe_recommendations.append(item)

        state.recommendations = safe_recommendations
        return "\n".join(intercepted) if intercepted else ""

    def _build_refer_message(self, triggered_keywords: List[str]) -> str:
        return (
            f"⚠️ 检测到可能的急危重症相关描述（{', '.join(triggered_keywords[:3])}等），"
            "本系统无法为此类情况提供建议。"
            "请立即拨打急救电话（120）或前往最近的急诊科就诊。"
        )

    def _llm_safety_review(self, state: SessionState) -> str:
        """使用 LLM 对建议文本进行语义级别的安全审查"""
        rec_text = "\n".join(
            f"- [{r.category}] {r.content}"
            for r in state.recommendations[:10]
        )
        system_prompt = build_system_prompt(
            "你是一名严格的中医健康建议安全审查员。"
            "你的任务是检查以下建议是否存在安全风险：明确处方剂量、不适合特殊人群的建议、"
            "可能误导患者放弃就医的内容。只输出发现的问题，如无问题输出'无'。"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"患者信息：{state.to_context_summary()}\n\n"
                    f"待审查的建议：\n{rec_text}\n\n"
                    "请列出发现的安全问题（如无问题，请输出'无'）："
                ),
            },
        ]
        result = self._call_llm(messages, temperature=0.1, max_tokens=512)
        result = result.strip()
        return "" if result.lower() in ("无", "no", "none", "") else result
