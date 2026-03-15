"""
SyndromeAgent —— 辨证分型智能体。

职责：
1. 综合症状、十问答案、望诊数据、RAG 检索结果进行辨证分型。
2. 输出候选证型列表，每个证型包含：
   - 名称、置信度、支持症状、RAG 证据片段、知识来源。
3. 确定主证型（置信度最高的候选）。
4. 实现"证据不足则继续追问"逻辑（设置 pending_questions）。

可解释性要求：
- 每条辨证结论必须关联到具体症状和 RAG 证据。
- 如果证据不足，明确标注"不确定"而非强行下结论。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from apps.agents.base_agent import BaseAgent, build_system_prompt
from apps.agents.session_state import (
    ConsultStage,
    ReferenceChunk,
    SessionState,
    SyndromeCandidate,
)

logger = logging.getLogger("apps.agents")

_SYNDROME_SYSTEM_PROMPT = build_system_prompt(
    """你是一名资深中医辨证专家。请根据提供的患者信息进行辨证分型分析。

输出要求（严格 JSON 格式）：
{
  "syndrome_candidates": [
    {
      "name": "证型名称（如：风寒束表证、气虚证）",
      "confidence": 0.85,
      "supporting_symptoms": ["支持该证型的症状1", "症状2"],
      "reasoning": "辨证推理过程（简要说明为何判断为此证型）",
      "classical_basis": "经典依据（如《伤寒论》相关条文，可为空）"
    }
  ],
  "primary_syndrome": "主证型名称（置信度最高的）",
  "constitution_inference": "体质推断（气虚质/阳虚质等，不确定则填null）",
  "insufficient_info": ["还需要了解的信息列表，如无则为空数组"],
  "evidence_summary": "综合证据摘要（简短说明辨证依据）"
}

重要规则：
1. 如果症状信息不足，confidence 不得超过 0.5，并在 insufficient_info 中列出需要补充的信息。
2. 证型名称必须使用标准中医术语。
3. 辨证结论不等于疾病诊断，禁止使用"诊断为XX病"的表述。
4. 只输出 JSON，不要包含其他文字。"""
)


class SyndromeAgent(BaseAgent):
    """辨证分型 Agent"""

    agent_name = "SyndromeAgent"
    stage = ConsultStage.SYNDROME

    # 主证型置信度阈值
    MIN_CONFIDENCE_THRESHOLD = 0.4

    def __init__(self, llm_caller=None, rag_retriever=None):
        """
        Parameters
        ----------
        rag_retriever : callable, optional
            签名：(query: str, top_k: int) -> List[ReferenceChunk]
        """
        super().__init__(llm_caller)
        self.rag_retriever = rag_retriever

    def _execute(self, state: SessionState, **kwargs) -> SessionState:
        new_state = state.model_copy(deep=True)

        # RAG 检索：用症状和主诉查询知识库
        rag_chunks = self._retrieve_rag_context(new_state)
        for chunk in rag_chunks:
            new_state.add_reference_chunk(chunk)

        # 构建辨证输入
        context_summary = new_state.to_context_summary()
        rag_text = self._format_rag_context(rag_chunks)

        # 构建望诊摘要
        obs = new_state.observation
        obs_lines: List[str] = []
        if obs.tongue_color:
            obs_lines.append(f"舌色：{obs.tongue_color}")
        if obs.tongue_coating:
            obs_lines.append(f"苔色：{obs.tongue_coating}")
        if obs.coating_thickness:
            obs_lines.append(f"苔厚薄：{obs.coating_thickness}")
        if obs.coating_texture:
            obs_lines.append(f"苔质：{obs.coating_texture}")
        if obs.tongue_shape:
            obs_lines.append(f"舌形：{obs.tongue_shape}")
        if obs.face_color:
            obs_lines.append(f"面色：{obs.face_color}")
        obs_text = "；".join(obs_lines) if obs_lines else "暂无望诊数据"

        messages = [
            {"role": "system", "content": _SYNDROME_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"【患者信息】\n{context_summary}\n\n"
                    f"【望诊数据】\n{obs_text}\n\n"
                    f"【知识库参考】\n{rag_text}\n\n"
                    "请进行辨证分型分析，以 JSON 格式返回："
                ),
            },
        ]

        raw = self._call_llm(messages, temperature=0.2, max_tokens=2048)
        data = self._parse_json_output(raw)

        new_state = self._update_state(new_state, data, rag_chunks)
        return new_state

    def _fallback(self, state: SessionState) -> SessionState:
        """降级：使用简单规则进行基础辨证"""
        new_state = state.model_copy(deep=True)

        # 极简规则降级
        symptom_names = {s.name for s in new_state.symptoms}
        candidates: List[SyndromeCandidate] = []

        # 简单规则匹配（与 apps/application/flow/tcm_tools.py 中的规则一致）
        rules = {
            "风寒束表证": {"怕冷", "流清涕", "无汗", "鼻塞"},
            "风热犯表证": {"发热", "咽痛", "流黄涕"},
            "气虚证": {"气短", "乏力", "懒言", "自汗"},
            "阴虚证": {"口干", "盗汗", "五心烦热", "失眠"},
        }
        for syndrome, required in rules.items():
            matches = symptom_names & required
            if matches:
                candidates.append(
                    SyndromeCandidate(
                        name=syndrome,
                        confidence=min(len(matches) / max(len(required), 1), 0.6),
                        supporting_symptoms=list(matches),
                        evidence_chunks=["（降级模式：基于简单规则匹配）"],
                    )
                )

        if candidates:
            candidates.sort(key=lambda c: c.confidence, reverse=True)
            new_state.syndrome_candidates = candidates
            new_state.primary_syndrome = candidates[0].name
        else:
            new_state.add_message(
                "assistant",
                "目前症状信息不足以进行准确辨证，建议您提供更多症状描述，"
                "或前往医疗机构就诊。",
            )

        new_state.current_stage = ConsultStage.RECOMMENDATION
        return new_state

    # ------------------------------------------------------------------
    # RAG 检索
    # ------------------------------------------------------------------

    def _retrieve_rag_context(self, state: SessionState) -> List[ReferenceChunk]:
        """执行 RAG 检索"""
        if not self.rag_retriever:
            return self._fallback_rag_retrieval(state)

        query_parts = [state.chief_complaint]
        query_parts.extend(s.name for s in state.symptoms[:5])
        query = "，".join(filter(None, query_parts))

        try:
            return self.rag_retriever(query, top_k=5)
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s", exc)
            return []

    def _fallback_rag_retrieval(self, state: SessionState) -> List[ReferenceChunk]:
        """
        当无 RAG 检索器时，尝试通过 Django ORM 进行向量检索。
        """
        try:
            from apps.knowledge.views import search_knowledge
            query = state.chief_complaint or " ".join(s.name for s in state.symptoms[:3])
            if not query.strip():
                return []

            results = search_knowledge(query, top_k=5)
            chunks: List[ReferenceChunk] = []
            for r in results:
                chunks.append(
                    ReferenceChunk(
                        content=r.get("content", ""),
                        source=r.get("source", "知识库"),
                        score=r.get("score", 0.0),
                        chunk_id=r.get("id"),
                    )
                )
            return chunks
        except Exception as exc:
            logger.debug("Fallback RAG retrieval failed: %s", exc)
            return []

    def _format_rag_context(self, chunks: List[ReferenceChunk]) -> str:
        if not chunks:
            return "（暂无相关知识库内容）"
        lines = []
        for i, chunk in enumerate(chunks[:5], 1):
            lines.append(f"[{i}] 来源：{chunk.source}\n{chunk.content[:400]}")
        return "\n\n".join(lines)

    # ------------------------------------------------------------------
    # 状态更新
    # ------------------------------------------------------------------

    def _update_state(
        self,
        state: SessionState,
        data: Dict[str, Any],
        rag_chunks: List[ReferenceChunk],
    ) -> SessionState:
        if not data:
            return state

        # 构建证型列表
        candidates: List[SyndromeCandidate] = []
        for cand in data.get("syndrome_candidates", []):
            if cand.get("name"):
                # 将 RAG 片段关联到证型
                evidence_texts = [c.content[:200] for c in rag_chunks[:3]]
                evidence_sources = [c.source for c in rag_chunks[:3]]
                candidates.append(
                    SyndromeCandidate(
                        name=cand["name"],
                        confidence=float(cand.get("confidence", 0.5)),
                        supporting_symptoms=cand.get("supporting_symptoms", []),
                        evidence_chunks=(
                            [cand.get("reasoning", "")]
                            + evidence_texts
                        ),
                        sources=evidence_sources,
                    )
                )

        state.syndrome_candidates = sorted(
            candidates, key=lambda c: c.confidence, reverse=True
        )

        # 主证型
        if data.get("primary_syndrome"):
            state.primary_syndrome = data["primary_syndrome"]
        elif candidates:
            state.primary_syndrome = candidates[0].name

        # 体质推断
        if data.get("constitution_inference"):
            for const in state.patient_profile.__class__.model_fields:
                pass
            # 尝试映射到枚举值
            from apps.agents.session_state import ConstitutionType
            constitution_str = data["constitution_inference"]
            for ct in ConstitutionType:
                if ct.value == constitution_str:
                    state.patient_profile.constitution = ct
                    break

        # 信息不足 → 继续追问
        insufficient = data.get("insufficient_info", [])
        if insufficient and (not state.primary_syndrome or
                              (candidates and candidates[0].confidence < self.MIN_CONFIDENCE_THRESHOLD)):
            state.pending_questions.extend(insufficient)
            state.current_stage = ConsultStage.INQUIRY
        else:
            state.current_stage = ConsultStage.RECOMMENDATION

        return state
