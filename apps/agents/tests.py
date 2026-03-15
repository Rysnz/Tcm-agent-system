"""
多智能体系统单元测试

覆盖范围：
1. SafetyGuardAgent - 关键词拦截、特殊人群、处方剂量拦截
2. SessionState - 状态机操作、序列化/反序列化
3. TCMOrchestrator - Agent 编排流程
4. RRF 混合检索逻辑（不依赖数据库）
"""
from unittest.mock import MagicMock, patch
from django.test import TestCase, RequestFactory

from apps.agents.safety_agent import (
    CRITICAL_KEYWORDS,
    HIGH_RISK_KEYWORDS,
    SafetyGuardAgent,
)
from apps.agents.session_state import (
    ConsultStage,
    PatientProfile,
    RecommendationItem,
    RiskLevel,
    SessionState,
    SymptomInfo,
)
from apps.agents.orchestrator import TCMOrchestrator


# ---------------------------------------------------------------------------
# 1. SessionState 测试
# ---------------------------------------------------------------------------

class SessionStateTest(TestCase):
    """会话状态机测试"""

    def test_initial_state(self):
        """新建状态应处于 INTAKE 阶段"""
        state = SessionState()
        self.assertEqual(state.current_stage, ConsultStage.INTAKE)
        self.assertFalse(state.is_high_risk)
        self.assertEqual(state.symptoms, [])

    def test_add_message(self):
        """添加消息应正确记录"""
        state = SessionState()
        state.add_message("user", "我头疼")
        state.add_message("assistant", "请问多久了？")
        self.assertEqual(len(state.messages), 2)
        self.assertEqual(state.messages[0]["role"], "user")
        self.assertEqual(state.messages[1]["content"], "请问多久了？")

    def test_mark_high_risk(self):
        """标记高风险后标志位和安全结果应正确设置"""
        state = SessionState()
        state.mark_high_risk("检测到胸痛症状")
        self.assertTrue(state.is_high_risk)
        self.assertEqual(state.safety_result.risk_level, RiskLevel.CRITICAL)
        self.assertTrue(state.safety_result.should_refer_immediately)
        self.assertIn("胸痛", state.safety_result.safety_message)

    def test_context_summary_with_pregnant(self):
        """妊娠期患者应在上下文摘要中体现"""
        state = SessionState()
        state.chief_complaint = "头晕"
        state.patient_profile.is_pregnant = True
        summary = state.to_context_summary()
        self.assertIn("妊娠期", summary)
        self.assertIn("头晕", summary)

    def test_serialize_deserialize(self):
        """序列化和反序列化应保持状态一致"""
        state = SessionState()
        state.chief_complaint = "失眠多梦"
        state.symptoms.append(SymptomInfo(name="失眠", duration="1周"))
        state.current_stage = ConsultStage.INQUIRY

        data = TCMOrchestrator.serialize_state(state)
        restored = TCMOrchestrator.restore_state(data)

        self.assertEqual(restored.chief_complaint, state.chief_complaint)
        self.assertEqual(len(restored.symptoms), 1)
        self.assertEqual(restored.symptoms[0].name, "失眠")
        self.assertEqual(restored.current_stage, ConsultStage.INQUIRY)

    def test_add_reference_chunk_dedup(self):
        """重复的 chunk 不应被重复添加"""
        from apps.agents.session_state import ReferenceChunk
        state = SessionState()
        chunk = ReferenceChunk(
            content="气虚则自汗", source="中医基础理论", chunk_id="chunk-001"
        )
        state.add_reference_chunk(chunk)
        state.add_reference_chunk(chunk)  # 重复添加
        self.assertEqual(len(state.reference_chunks), 1)


# ---------------------------------------------------------------------------
# 2. SafetyGuardAgent 测试
# ---------------------------------------------------------------------------

class SafetyGuardAgentTest(TestCase):
    """安全审查 Agent 测试"""

    def _make_state_with_complaint(self, complaint: str) -> SessionState:
        state = SessionState()
        state.chief_complaint = complaint
        state.add_message("user", complaint)
        return state

    def test_critical_keyword_chest_pain(self):
        """胸痛关键词应触发 CRITICAL 风险"""
        state = self._make_state_with_complaint("我突然感觉胸痛，非常剧烈")
        agent = SafetyGuardAgent(quick_check=True)
        result = agent.run(state)

        self.assertTrue(result.is_high_risk)
        self.assertEqual(result.safety_result.risk_level, RiskLevel.CRITICAL)
        self.assertTrue(result.safety_result.should_refer_immediately)
        self.assertIn("胸痛", result.safety_result.triggered_keywords)

    def test_critical_keyword_breathing_difficulty(self):
        """呼吸困难应触发 CRITICAL 风险"""
        state = self._make_state_with_complaint("呼吸困难，喘不过气")
        agent = SafetyGuardAgent(quick_check=True)
        result = agent.run(state)

        self.assertTrue(result.is_high_risk)
        self.assertTrue(result.safety_result.should_refer_immediately)

    def test_critical_keyword_hematemesis(self):
        """便血应触发 CRITICAL 风险"""
        state = self._make_state_with_complaint("大便有血，便血持续2天")
        agent = SafetyGuardAgent(quick_check=True)
        result = agent.run(state)

        self.assertTrue(result.is_high_risk)
        self.assertIn("便血", result.safety_result.triggered_keywords)

    def test_critical_keyword_consciousness_disorder(self):
        """意识障碍应触发 CRITICAL 风险"""
        state = self._make_state_with_complaint("患者出现意识障碍，无法正常交流")
        agent = SafetyGuardAgent(quick_check=True)
        result = agent.run(state)

        self.assertTrue(result.is_high_risk)

    def test_safe_common_symptom(self):
        """普通症状不应触发高风险"""
        state = self._make_state_with_complaint("最近感觉有点乏力，睡眠不好")
        agent = SafetyGuardAgent(quick_check=True)
        result = agent.run(state)

        self.assertFalse(result.is_high_risk)
        self.assertEqual(result.safety_result.risk_level, RiskLevel.LOW)

    def test_pregnant_woman_flag(self):
        """妊娠期妇女应被标记"""
        state = SessionState()
        state.patient_profile.is_pregnant = True
        state.chief_complaint = "头晕"
        agent = SafetyGuardAgent(quick_check=True)
        result = agent.run(state)

        self.assertIn("妊娠期妇女", result.safety_result.special_population_flags)

    def test_minor_flag(self):
        """未成年人应被标记"""
        state = SessionState()
        state.patient_profile.is_minor = True
        state.chief_complaint = "头疼发烧"
        agent = SafetyGuardAgent(quick_check=True)
        result = agent.run(state)

        self.assertIn("未成年人", result.safety_result.special_population_flags)

    def test_prescription_dose_interception(self):
        """含明确剂量的建议应被拦截"""
        state = SessionState()
        state.chief_complaint = "气虚乏力"
        state.recommendations = [
            RecommendationItem(
                category="中药建议",
                content="黄芪30g，党参20g，水煎服，每日一剂",
                rationale="补气健脾",
            )
        ]
        agent = SafetyGuardAgent(quick_check=True)
        result = agent.run(state)

        # 拦截后建议内容应不含剂量，应含免责说明
        if result.recommendations:
            for rec in result.recommendations:
                self.assertNotIn("水煎服，每日一剂", rec.content)
                if "中药建议" in rec.category:
                    self.assertIn("执业中医师", rec.content)

    def test_critical_risk_clears_recommendations(self):
        """高风险状态下，建议列表应被清空并替换为就医提示"""
        state = SessionState()
        state.chief_complaint = "胸痛剧烈"
        state.add_message("user", "胸痛剧烈")
        state.recommendations = [
            RecommendationItem(category="饮食", content="多喝水"),
            RecommendationItem(category="运动", content="散步"),
        ]
        agent = SafetyGuardAgent(quick_check=True)
        result = agent.run(state)

        # 高风险后建议列表只剩安全提示
        self.assertTrue(result.is_high_risk)
        self.assertEqual(len(result.recommendations), 1)
        self.assertEqual(result.recommendations[0].category, "安全提示")

    def test_high_risk_keywords_detection(self):
        """高风险（非紧急）关键词应触发 HIGH 风险"""
        state = self._make_state_with_complaint("持续发烧3天，咳血少量")
        agent = SafetyGuardAgent(quick_check=True)
        result = agent.run(state)

        # 咳血是 HIGH_RISK_KEYWORDS 之一
        self.assertIn(result.safety_result.risk_level, [RiskLevel.HIGH, RiskLevel.CRITICAL])

    def test_all_critical_keywords_are_strings(self):
        """确保关键词列表中所有元素都是字符串"""
        for kw in CRITICAL_KEYWORDS:
            self.assertIsInstance(kw, str, f"Critical keyword not a string: {kw}")
        for kw in HIGH_RISK_KEYWORDS:
            self.assertIsInstance(kw, str, f"High risk keyword not a string: {kw}")


# ---------------------------------------------------------------------------
# 3. IntakeAgent 测试（Mock LLM）
# ---------------------------------------------------------------------------

class IntakeAgentTest(TestCase):
    """接诊 Agent 测试（使用 Mock LLM）"""

    def _make_mock_llm(self, response_json: str):
        """创建返回固定 JSON 的 mock LLM"""
        return MagicMock(return_value=response_json)

    def test_extract_chief_complaint(self):
        """应从用户消息中提取主诉"""
        from apps.agents.intake_agent import IntakeAgent

        mock_response = '''
        {
          "chief_complaint": "头痛伴发热",
          "symptoms": [
            {"name": "头痛", "duration": "2天", "severity": "中", "onset": "急"},
            {"name": "发热", "duration": "2天", "severity": "轻", "onset": "急"}
          ],
          "age_group": "青年",
          "gender": "男",
          "is_pregnant": false,
          "is_minor": false,
          "medical_history": [],
          "current_medications": [],
          "needs_clarification": []
        }
        '''
        agent = IntakeAgent(llm_caller=self._make_mock_llm(mock_response))

        state = SessionState()
        state.add_message("user", "我头痛发烧两天了，很不舒服")
        result = agent.run(state)

        self.assertEqual(result.chief_complaint, "头痛伴发热")
        self.assertEqual(len(result.symptoms), 2)
        self.assertEqual(result.symptoms[0].name, "头痛")
        self.assertEqual(result.patient_profile.gender, "男")
        self.assertEqual(result.current_stage, ConsultStage.INQUIRY)

    def test_no_user_message_returns_greeting(self):
        """没有用户消息时应返回欢迎语"""
        from apps.agents.intake_agent import IntakeAgent

        agent = IntakeAgent(llm_caller=self._make_mock_llm("{}"))
        state = SessionState()
        result = agent.run(state)

        assistant_msgs = [m for m in result.messages if m["role"] == "assistant"]
        self.assertTrue(len(assistant_msgs) > 0)

    def test_fallback_on_llm_error(self):
        """LLM 调用失败时应使用降级策略"""
        from apps.agents.intake_agent import IntakeAgent

        def failing_llm(*args, **kwargs):
            raise RuntimeError("LLM service unavailable")

        agent = IntakeAgent(llm_caller=failing_llm)
        agent.max_retries = 0  # 不重试，直接降级
        state = SessionState()
        state.add_message("user", "头疼很厉害")
        result = agent.run(state)

        # 降级后应有内容（chief_complaint 或 assistant 消息）
        self.assertTrue(
            result.chief_complaint or
            any(m["role"] == "assistant" for m in result.messages)
        )


# ---------------------------------------------------------------------------
# 4. Orchestrator 编排测试
# ---------------------------------------------------------------------------

class OrchestratorTest(TestCase):
    """编排器集成测试"""

    def _make_mock_llm_factory(self, responses: dict):
        """
        根据关键词返回不同响应的 mock LLM。
        responses: {"keyword_in_prompt": "json_response"}
        """
        def mock_llm(messages, **kwargs):
            # 找到最后一条 user 消息
            last_user = ""
            for m in reversed(messages):
                if m.get("role") in ("user", "system"):
                    last_user = m.get("content", "")
                    break
            for keyword, response in responses.items():
                if keyword in last_user:
                    return response
            return "{}"
        return mock_llm

    def test_create_session(self):
        """创建会话应初始化 INTAKE 阶段"""
        orch = TCMOrchestrator()
        state = orch.create_session()
        self.assertEqual(state.current_stage, ConsultStage.INTAKE)
        self.assertIsNotNone(state.session_id)

    def test_high_risk_message_triggers_safety(self):
        """高风险消息应触发安全中断"""
        orch = TCMOrchestrator(llm_caller=MagicMock(return_value="{}"))
        state = orch.create_session()

        # 发送胸痛描述（快速安全预检无需 LLM）
        result = orch.process_message(state, "我突然胸痛剧烈")
        self.assertTrue(result.is_high_risk)

    def test_serialize_restore_cycle(self):
        """编排器应能序列化并恢复会话状态"""
        orch = TCMOrchestrator()
        state = orch.create_session()
        state.chief_complaint = "气短乏力"
        state.current_stage = ConsultStage.SYNDROME

        serialized = TCMOrchestrator.serialize_state(state)
        restored = TCMOrchestrator.restore_state(serialized)

        self.assertEqual(restored.session_id, state.session_id)
        self.assertEqual(restored.chief_complaint, "气短乏力")
        self.assertEqual(restored.current_stage, ConsultStage.SYNDROME)

    def test_max_inquiry_rounds_prevents_infinite_loop(self):
        """超过最大追问轮数应强制推进到辨证阶段"""
        # Mock LLM 总是返回"信息不足"
        mock_response = '{"questions": ["请再说说"], "is_sufficient": false, "new_symptoms": [], "inquiry_answers": {}}'
        orch = TCMOrchestrator(
            llm_caller=MagicMock(return_value=mock_response),
            max_inquiry_rounds=2,
        )
        state = orch.create_session()
        state.current_stage = ConsultStage.INQUIRY
        state.chief_complaint = "头疼"

        # 模拟超过最大追问轮数
        from apps.agents.session_state import AgentCallRecord
        from datetime import datetime
        for _ in range(3):
            state.agent_call_records.append(
                AgentCallRecord(
                    agent_name="InquiryAgent",
                    stage=ConsultStage.INQUIRY,
                    started_at=datetime.utcnow(),
                    finished_at=datetime.utcnow(),
                    success=True,
                )
            )

        result = orch._route(state)
        # 超过上限后应推进到 SYNDROME 或更后
        self.assertNotEqual(result.current_stage, ConsultStage.INQUIRY)


# ---------------------------------------------------------------------------
# 5. RRF 混合检索测试（纯逻辑，不依赖数据库）
# ---------------------------------------------------------------------------

class RRFBlendSearchTest(TestCase):
    """RRF 混合检索逻辑测试"""

    def _compute_rrf(self, embedding_results, keywords_results, k=5, rrf_k=60):
        """内联 RRF 计算逻辑（与 pg_vector.py 保持一致）"""
        embedding_rank = {r['id']: idx + 1 for idx, r in enumerate(embedding_results)}
        keywords_rank = {r['id']: idx + 1 for idx, r in enumerate(keywords_results)}
        all_ids = set(embedding_rank.keys()) | set(keywords_rank.keys())

        doc_map = {}
        for r in embedding_results:
            doc_map[r['id']] = r
        for r in keywords_results:
            if r['id'] not in doc_map:
                doc_map[r['id']] = r

        rrf_scores = {}
        for doc_id in all_ids:
            score = 0.0
            if doc_id in embedding_rank:
                score += 1.0 / (rrf_k + embedding_rank[doc_id])
            if doc_id in keywords_rank:
                score += 1.0 / (rrf_k + keywords_rank[doc_id])
            rrf_scores[doc_id] = score

        sorted_ids = sorted(all_ids, key=lambda did: rrf_scores[did], reverse=True)
        results = []
        for doc_id in sorted_ids[:k]:
            doc = doc_map[doc_id].copy()
            doc['score'] = rrf_scores[doc_id]
            results.append(doc)
        return results

    def test_rrf_both_sources_ranked_higher(self):
        """同时出现在两个排名中的文档应获得更高的 RRF 分数"""
        embedding = [
            {'id': 'doc1', 'content': 'A', 'score': 0.9, 'title': None, 'page_number': None, 'metadata': {}},
            {'id': 'doc2', 'content': 'B', 'score': 0.7, 'title': None, 'page_number': None, 'metadata': {}},
            {'id': 'doc3', 'content': 'C', 'score': 0.5, 'title': None, 'page_number': None, 'metadata': {}},
        ]
        keywords = [
            {'id': 'doc2', 'content': 'B', 'score': 0.9, 'title': None, 'page_number': None, 'metadata': {}},
            {'id': 'doc4', 'content': 'D', 'score': 0.8, 'title': None, 'page_number': None, 'metadata': {}},
            {'id': 'doc1', 'content': 'A', 'score': 0.6, 'title': None, 'page_number': None, 'metadata': {}},
        ]
        results = self._compute_rrf(embedding, keywords)
        result_ids = [r['id'] for r in results]

        # doc1 在 embedding 排名1，keywords 排名3 → 较高 RRF
        # doc2 在 embedding 排名2，keywords 排名1 → 最高 RRF
        # doc2 应排在前面（出现在两个列表的前位）
        self.assertIn('doc2', result_ids[:2])
        self.assertIn('doc1', result_ids[:2])

    def test_rrf_unique_document_included(self):
        """只出现在一个列表中的文档也应被包含"""
        embedding = [
            {'id': 'doc1', 'content': 'A', 'score': 0.9, 'title': None, 'page_number': None, 'metadata': {}},
        ]
        keywords = [
            {'id': 'doc2', 'content': 'B', 'score': 0.9, 'title': None, 'page_number': None, 'metadata': {}},
        ]
        results = self._compute_rrf(embedding, keywords)
        result_ids = {r['id'] for r in results}
        self.assertIn('doc1', result_ids)
        self.assertIn('doc2', result_ids)

    def test_rrf_score_range(self):
        """所有 RRF 分数应在有效范围内（> 0）"""
        embedding = [
            {'id': f'doc{i}', 'content': f'Content{i}', 'score': 0.9 - i * 0.1,
             'title': None, 'page_number': None, 'metadata': {}}
            for i in range(5)
        ]
        results = self._compute_rrf(embedding, [])
        for r in results:
            self.assertGreater(r['score'], 0)

    def test_rrf_top_k_limit(self):
        """返回结果数量不应超过 k"""
        embedding = [
            {'id': f'doc{i}', 'content': f'C{i}', 'score': 1.0 - i * 0.1,
             'title': None, 'page_number': None, 'metadata': {}}
            for i in range(10)
        ]
        results = self._compute_rrf(embedding, [], k=3)
        self.assertLessEqual(len(results), 3)
