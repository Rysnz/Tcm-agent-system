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

【重要】只输出JSON，不要输出任何解释、思考过程或其他文字！

【辨证原则】
1. 主要依据：症状描述、十问答案、望诊数据（如有）
2. 辅助依据：RAG检索的中医知识
3. 辨证方法：八纲辨证（阴阳、表里、寒热、虚实）为主

【关于舌象和脉象】
- 舌象：如果系统提供了舌象分析结果，请作为重要参考依据
- 脉象：本系统暂不采集脉象信息，请基于其他四诊信息进行辨证
- 如果舌象信息不足，请基于症状和问诊信息进行辨证，不要要求补充脉象信息

【辨证思路】
1. 首先分析主诉和主要症状
2. 结合十问答案判断寒热虚实
3. 如有望诊数据，综合分析
4. 参考RAG知识进行证型匹配
5. 给出置信度和辨证依据

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
4. 不要要求补充舌象或脉象信息，基于现有信息进行辨证。
5. 只输出 JSON，不要包含其他文字。"""
)


class SyndromeAgent(BaseAgent):
    """辨证分型 Agent"""

    agent_name = "SyndromeAgent"
    stage = ConsultStage.SYNDROME

    # 主证型置信度阈值（从0.4提高到0.5，确保辨证质量）
    MIN_CONFIDENCE_THRESHOLD = 0.5

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
        if not data:
            raise ValueError("SyndromeAgent 未获取到可解析的结构化输出")

        new_state = self._update_state(new_state, data, rag_chunks)
        return new_state

    def _fallback(self, state: SessionState) -> SessionState:
        """降级：使用简单规则进行基础辨证"""
        new_state = state.model_copy(deep=True)

        # 极简规则降级
        symptom_names = {s.name for s in new_state.symptoms}
        
        # 也从inquiry_answers中提取症状
        for key, value in new_state.inquiry_answers.items():
            if value and isinstance(value, str):
                # 简单的关键词提取
                for symptom in ["头痛", "头疼", "头晕", "失眠", "盗汗", "自汗", "怕冷", "怕热", 
                               "大便干燥", "大便稀溏", "食欲不振", "乏力", "气短", "口干", "口苦"]:
                    if symptom in value:
                        symptom_names.add(symptom)
        
        # 从chief_complaint中提取症状
        if new_state.chief_complaint:
            for symptom in ["头痛", "头疼", "头晕", "失眠", "盗汗", "自汗", "怕冷", "怕热",
                           "大便干燥", "大便稀溏", "食欲不振", "乏力", "气短", "口干", "口苦",
                           "手脚冰凉", "手足冰凉", "四肢冰凉"]:
                if symptom in new_state.chief_complaint:
                    symptom_names.add(symptom)
        
        # 从消息历史中提取症状
        for msg in new_state.messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                for symptom in ["头痛", "头疼", "头晕", "失眠", "盗汗", "自汗", "怕冷", "怕热",
                               "大便干燥", "大便稀溏", "食欲不振", "乏力", "气短", "口干", "口苦",
                               "手脚冰凉", "手足冰凉", "四肢冰凉"]:
                    if symptom in content:
                        symptom_names.add(symptom)
        
        # 打印调试信息
        import sys
        print(f"[DEBUG] SyndromeAgent Fallback extracted symptoms: {symptom_names}", file=sys.stderr)
        print(f"[DEBUG] SyndromeAgent Fallback symptoms from state.symptoms: {[s.name for s in new_state.symptoms]}", file=sys.stderr)
        print(f"[DEBUG] SyndromeAgent Fallback inquiry_answers: {new_state.inquiry_answers}", file=sys.stderr)
        print(f"[DEBUG] SyndromeAgent Fallback chief_complaint: {new_state.chief_complaint}", file=sys.stderr)
        print(f"[DEBUG] SyndromeAgent Fallback messages: {[m.get('content', '')[:50] for m in new_state.messages if m.get('role') == 'user']}", file=sys.stderr)
        
        candidates: List[SyndromeCandidate] = []

        # 扩展规则匹配
        # 每个规则包含：必须症状集合（至少匹配一个）和可选症状集合
        rules = {
            "风寒束表证": {
                "required": {"怕冷", "流清涕", "无汗", "鼻塞"},
                "min_match": 1,
                "weight": 0.6
            },
            "风热犯表证": {
                "required": {"发热", "咽痛", "流黄涕"},
                "min_match": 1,
                "weight": 0.6
            },
            "气虚证": {
                "required": {"气短", "乏力", "懒言", "自汗", "食欲不振"},
                "min_match": 2,
                "weight": 0.65
            },
            "阴虚证": {
                "required": {"口干", "盗汗", "五心烦热", "失眠", "手脚心热"},
                "min_match": 2,
                "weight": 0.7
            },
            "血虚证": {
                "required": {"面色苍白", "头晕", "心悸", "失眠", "乏力"},
                "min_match": 2,
                "weight": 0.65
            },
            "阳虚证": {
                "required": {"怕冷", "手脚冰凉", "手足冰凉", "四肢冰凉", "乏力", "大便稀溏"},
                "min_match": 2,
                "weight": 0.65
            },
            "肝郁气滞证": {
                "required": {"情志抑郁", "胸胁胀痛", "善太息", "烦躁易怒"},
                "min_match": 1,
                "weight": 0.6
            },
            "脾胃虚弱证": {
                "required": {"食欲不振", "腹胀", "大便稀溏", "乏力", "大便干燥"},
                "min_match": 2,
                "weight": 0.65
            },
            "阴虚火旺证": {
                "required": {"盗汗", "失眠", "口干", "手脚心热", "烦躁"},
                "min_match": 2,
                "weight": 0.7
            },
            "气阴两虚证": {
                "required": {"乏力", "气短", "盗汗", "口干", "失眠"},
                "min_match": 3,
                "weight": 0.75
            },
            # 新增证型：覆盖更多症状组合
            "肝阳上亢证": {
                "required": {"头疼", "头晕", "烦躁易怒", "面红目赤", "口苦"},
                "min_match": 2,
                "weight": 0.7
            },
            "肝肾阴虚证": {
                "required": {"头晕", "耳鸣", "腰膝酸软", "盗汗", "失眠"},
                "min_match": 2,
                "weight": 0.7
            },
            "脾肾阳虚证": {
                "required": {"怕冷", "手脚冰凉", "腰膝酸软", "大便稀溏", "乏力"},
                "min_match": 2,
                "weight": 0.7
            },
            "血瘀证": {
                "required": {"刺痛", "固定痛", "面色晦暗", "舌紫暗", "肌肤甲错"},
                "min_match": 2,
                "weight": 0.7
            },
            "痰湿证": {
                "required": {"胸闷", "痰多", "身体困重", "食欲不振", "大便粘腻"},
                "min_match": 2,
                "weight": 0.7
            },
            "湿热证": {
                "required": {"口苦", "口干", "身热不扬", "汗出不畅", "大便粘腻"},
                "min_match": 2,
                "weight": 0.7
            },
        }
        
        for syndrome, rule in rules.items():
            required = rule["required"]
            min_match = rule.get("min_match", 1)
            weight = rule.get("weight", 0.6)
            
            matches = symptom_names & required
            if len(matches) >= min_match:
                # 计算匹配度
                match_ratio = len(matches) / len(required)
                confidence = min(match_ratio * weight + (len(matches) * 0.05), 0.75)
                
                candidates.append(
                    SyndromeCandidate(
                        name=syndrome,
                        confidence=confidence,
                        supporting_symptoms=list(matches),
                        evidence_chunks=["（降级模式：基于简单规则匹配）"],
                    )
                )

        # 如果没有匹配的证型，使用"其他证型"
        if not candidates:
            candidates.append(
                SyndromeCandidate(
                    name="其他证型",
                    confidence=0.5,
                    supporting_symptoms=list(symptom_names),
                    evidence_chunks=["（降级模式：症状组合特殊，无法精确匹配）"],
                )
            )

        if candidates:
            candidates.sort(key=lambda c: c.confidence, reverse=True)
            new_state.syndrome_candidates = candidates
            new_state.primary_syndrome = candidates[0].name
            print(f"[DEBUG] SyndromeAgent Fallback syndrome: {candidates[0].name}, confidence: {candidates[0].confidence:.2f}", file=sys.stderr)
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
        """
        执行 RAG 检索
        
        返回值：
        - 成功检索到结果：返回ReferenceChunk列表
        - 检索成功但无相关结果：返回空列表
        - 检索失败：抛出异常或返回包含错误标记的特殊chunk
        """
        if not self.rag_retriever:
            return self._fallback_rag_retrieval(state)

        query_parts = [state.chief_complaint]
        query_parts.extend(s.name for s in state.symptoms[:5])
        query = "，".join(filter(None, query_parts))
        
        if not query.strip():
            logger.warning("RAG query is empty, skipping retrieval")
            return []

        try:
            results = self.rag_retriever(query, top_k=5)
            
            # 验证检索结果的有效性
            if results is None:
                logger.error("RAG retriever returned None")
                return []
            
            # 过滤掉空内容的结果
            valid_results = [r for r in results if r and r.content and r.content.strip()]
            
            if not valid_results and results:
                logger.warning("RAG retriever returned %d results but all are empty", len(results))
            
            return valid_results
            
        except ConnectionError as exc:
            logger.error("RAG retrieval connection error: %s", exc)
            # 连接错误：可能是数据库或向量服务不可用
            return []
        except TimeoutError as exc:
            logger.error("RAG retrieval timeout: %s", exc)
            # 超时错误
            return []
        except Exception as exc:
            logger.error("RAG retrieval unexpected error: %s", exc, exc_info=True)
            # 其他未知错误
            return []

    def _fallback_rag_retrieval(self, state: SessionState) -> List[ReferenceChunk]:
        """
        当无 RAG 检索器时，尝试通过 Django ORM 进行向量检索。
        只检索启用的知识库。
        """
        try:
            from apps.knowledge.models import KnowledgeBase
            from apps.knowledge.vector.pg_vector import PGVectorStore
            
            query = state.chief_complaint or " ".join(s.name for s in state.symptoms[:3])
            if not query.strip():
                return []

            # 获取所有启用的知识库
            active_kbs = KnowledgeBase.objects.filter(is_active=True, is_delete=False)
            
            if not active_kbs.exists():
                logger.debug("No active knowledge base found")
                return []
            
            chunks: List[ReferenceChunk] = []
            
            # 对每个启用的知识库进行检索
            for kb in active_kbs[:3]:  # 最多检索3个知识库
                try:
                    config = {
                        'knowledge_base_id': str(kb.id),
                        'embedding_model': kb.embedding_model,
                        'dimension': kb.embedding_dimension
                    }
                    vector_store = PGVectorStore(config)
                    
                    # 使用关键词检索（更可靠）
                    results = vector_store.similarity_search(query, k=3, search_type='keywords')
                    
                    for r in results:
                        if r.get("content"):
                            chunks.append(
                                ReferenceChunk(
                                    content=r.get("content", ""),
                                    source=r.get("source", f"知识库:{kb.name}"),
                                    score=r.get("score", 0.0),
                                    chunk_id=r.get("id"),
                                )
                            )
                except Exception as e:
                    logger.warning(f"Failed to search knowledge base {kb.name}: {e}")
                    continue
            
            logger.info(f"RAG retrieval found {len(chunks)} chunks from {active_kbs.count()} knowledge bases")
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
            from apps.agents.session_state import ConstitutionType
            constitution_str = data["constitution_inference"]
            
            # 支持精确匹配和模糊匹配
            matched = False
            
            # 1. 精确匹配
            for ct in ConstitutionType:
                if ct.value == constitution_str:
                    state.patient_profile.constitution = ct
                    matched = True
                    break
            
            # 2. 如果精确匹配失败，尝试模糊匹配
            if not matched:
                # 同义词映射
                constitution_aliases = {
                    "气虚": "气虚质",
                    "阳虚": "阳虚质",
                    "阴虚": "阴虚质",
                    "痰湿": "痰湿质",
                    "湿热": "湿热质",
                    "血瘀": "血瘀质",
                    "气郁": "气郁质",
                    "特禀": "特禀质",
                    "平和": "平和质",
                    "平和体质": "平和质",
                    "气虚体质": "气虚质",
                    "阳虚体质": "阳虚质",
                    "阴虚体质": "阴虚质",
                    "痰湿体质": "痰湿质",
                    "湿热体质": "湿热质",
                    "血瘀体质": "血瘀质",
                    "气郁体质": "气郁质",
                    "特禀体质": "特禀质",
                }
                
                # 先检查别名
                if constitution_str in constitution_aliases:
                    target_value = constitution_aliases[constitution_str]
                    for ct in ConstitutionType:
                        if ct.value == target_value:
                            state.patient_profile.constitution = ct
                            matched = True
                            break
                
                # 如果还是没匹配上，尝试包含匹配
                if not matched:
                    for ct in ConstitutionType:
                        if constitution_str in ct.value or ct.value in constitution_str:
                            state.patient_profile.constitution = ct
                            matched = True
                            break

        # 信息不足 → 继续追问
        insufficient = data.get("insufficient_info", [])
        if insufficient and (not state.primary_syndrome or
                              (candidates and candidates[0].confidence < self.MIN_CONFIDENCE_THRESHOLD)):
            uniq_questions: List[str] = []
            for q in insufficient:
                q_text = str(q or "").strip()
                if q_text and q_text not in uniq_questions:
                    uniq_questions.append(q_text)
            state.pending_questions = uniq_questions[:2]
            if state.pending_questions:
                state.add_message(
                    "assistant",
                    "\n".join(
                        f"{i + 1}. {q}" for i, q in enumerate(state.pending_questions)
                    ),
                )
            state.current_stage = ConsultStage.INQUIRY
        else:
            state.current_stage = ConsultStage.RECOMMENDATION

        return state
