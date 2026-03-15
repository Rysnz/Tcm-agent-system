"""
ReportAgent —— 报告生成智能体。

职责：
1. 汇总整个问诊流程的所有信息。
2. 生成结构化 JSON 报告（report_json）。
3. 生成人类可读的文本报告（report_text）。
4. 附加完整的证据链：症状 → 证型 → 建议 → RAG来源。
5. 强制附加免责声明。
6. 若存在高风险，在报告开头突出展示就医建议。
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

from apps.agents.base_agent import BaseAgent, build_system_prompt
from apps.agents.session_state import ConsultStage, SessionState

logger = logging.getLogger("apps.agents")

_REPORT_SYSTEM_PROMPT = build_system_prompt(
    """你是一名中医问诊报告撰写专家。请根据完整的问诊信息，
生成一份结构清晰、专业规范的问诊报告。

输出格式（严格 JSON）：
{
  "report_title": "中医智能问诊报告",
  "patient_summary": "患者信息摘要（年龄段、性别、主诉）",
  "symptom_analysis": "症状分析（列出主要症状及特点）",
  "observation_findings": "望诊所见（舌象/面色等，无则说明'暂无望诊数据'）",
  "syndrome_conclusion": {
    "primary_syndrome": "主证型",
    "confidence": 0.0,
    "evidence": ["证据1（症状+依据）", "证据2"]
  },
  "recommendations_summary": "调理建议摘要",
  "safety_notes": "安全提示（如有高风险必须突出）",
  "evidence_chain": "完整证据链（症状→证型→建议→知识来源）",
  "references": ["参考来源1", "参考来源2"],
  "follow_up_suggestions": "随访建议",
  "disclaimer": "免责声明（必须包含）"
}

要求：
1. 报告内容需完整、专业、通俗易懂。
2. 证据链必须清晰，每条结论都能追溯到具体症状和参考依据。
3. 免责声明必须明确：本报告为健康建议，不构成医疗诊断。
4. 只输出 JSON，不要包含其他文字。"""
)


class ReportAgent(BaseAgent):
    """报告生成 Agent"""

    agent_name = "ReportAgent"
    stage = ConsultStage.REPORT

    def _execute(self, state: SessionState, **kwargs) -> SessionState:
        new_state = state.model_copy(deep=True)

        # 构建完整问诊摘要
        full_summary = self._build_full_summary(new_state)

        messages = [
            {"role": "system", "content": _REPORT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"请根据以下完整问诊记录生成报告：\n\n{full_summary}"
                ),
            },
        ]

        raw = self._call_llm(messages, temperature=0.2, max_tokens=3000)
        data = self._parse_json_output(raw)

        # 更新状态
        new_state.report_json = data
        new_state.report_text = self._format_readable_report(new_state, data)
        new_state.current_stage = ConsultStage.DONE

        # 将报告添加为助手消息
        new_state.add_message("assistant", new_state.report_text)

        return new_state

    def _fallback(self, state: SessionState) -> SessionState:
        """降级：生成简化版报告"""
        new_state = state.model_copy(deep=True)
        report_text = self._build_simple_report(new_state)
        new_state.report_text = report_text
        new_state.report_json = {"report_text": report_text, "fallback": True}
        new_state.current_stage = ConsultStage.DONE
        new_state.add_message("assistant", report_text)
        return new_state

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------

    def _build_full_summary(self, state: SessionState) -> str:
        lines: List[str] = [
            "=== 完整问诊记录 ===",
            f"会话ID：{state.session_id}",
            f"问诊时间：{state.created_at.strftime('%Y-%m-%d %H:%M')}",
            "",
            "【患者信息】",
            state.to_context_summary(),
            "",
            "【症状详情】",
        ]
        for sym in state.symptoms:
            detail = f"  - {sym.name}"
            if sym.duration:
                detail += f"（{sym.duration}）"
            if sym.severity:
                detail += f" [{sym.severity}]"
            lines.append(detail)

        lines.append("\n【十问答案】")
        for k, v in state.inquiry_answers.items():
            lines.append(f"  {k}: {v}")

        obs = state.observation
        if any([obs.tongue_color, obs.tongue_coating, obs.face_color]):
            lines.append("\n【望诊数据】")
            if obs.tongue_color:
                lines.append(f"  舌色：{obs.tongue_color}")
            if obs.tongue_coating:
                lines.append(f"  苔色：{obs.tongue_coating}")
            if obs.coating_thickness:
                lines.append(f"  苔厚薄：{obs.coating_thickness}")
            if obs.coating_texture:
                lines.append(f"  苔质：{obs.coating_texture}")
            if obs.tongue_shape:
                lines.append(f"  舌形：{obs.tongue_shape}")
            if obs.face_color:
                lines.append(f"  面色：{obs.face_color}")

        lines.append("\n【辨证结果】")
        for cand in state.syndrome_candidates[:3]:
            lines.append(
                f"  {cand.name}（置信度：{cand.confidence:.0%}）"
                f" - 支持症状：{', '.join(cand.supporting_symptoms[:4])}"
            )

        lines.append("\n【调理建议】")
        for rec in state.recommendations:
            lines.append(f"  [{rec.category}] {rec.content}")
            if rec.rationale:
                lines.append(f"    依据：{rec.rationale}")

        if state.reference_chunks:
            lines.append("\n【参考文献（前3条）】")
            for chunk in state.reference_chunks[:3]:
                lines.append(f"  来源：{chunk.source}")
                lines.append(f"  内容：{chunk.content[:150]}...")

        if state.safety_result.safety_message:
            lines.append("\n【安全提示】")
            lines.append(f"  {state.safety_result.safety_message}")

        return "\n".join(lines)

    def _format_readable_report(
        self, state: SessionState, data: Dict[str, Any]
    ) -> str:
        """将 JSON 报告格式化为可读文本"""
        if not data:
            return self._build_simple_report(state)

        parts: List[str] = []

        # 高风险优先展示
        if state.is_high_risk:
            parts.append(
                "⚠️ ══════════════════════════════\n"
                "   高风险提示：请立即就医\n"
                "══════════════════════════════ ⚠️\n"
            )
            if state.safety_result.safety_message:
                parts.append(state.safety_result.safety_message + "\n")

        parts.append(f"📋 {data.get('report_title', '中医智能问诊报告')}")
        parts.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

        if data.get("patient_summary"):
            parts.append(f"👤 患者信息\n{data['patient_summary']}\n")

        if data.get("symptom_analysis"):
            parts.append(f"🔍 症状分析\n{data['symptom_analysis']}\n")

        if data.get("observation_findings"):
            parts.append(f"👁️ 望诊所见\n{data['observation_findings']}\n")

        # 辨证结论
        syndrome = data.get("syndrome_conclusion", {})
        if syndrome:
            parts.append("🎯 辨证结论")
            parts.append(f"主证型：{syndrome.get('primary_syndrome', '未明确')}")
            conf = syndrome.get("confidence", 0)
            if conf:
                parts.append(f"置信度：{float(conf):.0%}")
            evidence = syndrome.get("evidence", [])
            if evidence:
                parts.append("支持依据：")
                for ev in evidence[:4]:
                    parts.append(f"  • {ev}")
            parts.append("")

        if data.get("recommendations_summary"):
            parts.append(f"💊 调理建议\n{data['recommendations_summary']}\n")

        # 详细建议列表
        if state.recommendations:
            parts.append("📌 详细建议")
            for rec in state.recommendations:
                parts.append(f"  【{rec.category}】{rec.content}")
                if rec.caution:
                    parts.append(f"    ⚠️ 注意：{rec.caution}")
            parts.append("")

        if data.get("evidence_chain"):
            parts.append(f"🔗 证据链\n{data['evidence_chain']}\n")

        if state.reference_chunks:
            parts.append("📚 参考依据")
            seen = set()
            for chunk in state.reference_chunks[:5]:
                if chunk.source and chunk.source not in seen:
                    parts.append(f"  [{chunk.source}] {chunk.content[:100]}...")
                    seen.add(chunk.source)
            parts.append("")

        if data.get("follow_up_suggestions"):
            parts.append(f"📅 随访建议\n{data['follow_up_suggestions']}\n")

        if data.get("safety_notes"):
            parts.append(f"⚠️ 安全提示\n{data['safety_notes']}\n")

        # 免责声明（强制附加）
        parts.append("─" * 40)
        parts.append(state.disclaimer)

        return "\n".join(parts)

    def _build_simple_report(self, state: SessionState) -> str:
        """降级版简化报告"""
        lines: List[str] = [
            "📋 中医智能问诊报告（简化版）",
            f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
        ]

        if state.is_high_risk and state.safety_result.safety_message:
            lines.append("⚠️ " + state.safety_result.safety_message)
            lines.append("")

        if state.chief_complaint:
            lines.append(f"主诉：{state.chief_complaint}")

        if state.primary_syndrome:
            lines.append(f"辨证：{state.primary_syndrome}")

        if state.recommendations:
            lines.append("\n调理建议：")
            for rec in state.recommendations[:5]:
                lines.append(f"• [{rec.category}] {rec.content}")

        lines.append("")
        lines.append(state.disclaimer)
        return "\n".join(lines)
