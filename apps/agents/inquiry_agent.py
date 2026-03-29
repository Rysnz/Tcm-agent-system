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
import re
from typing import Any, Dict, List, Optional

from apps.agents.base_agent import BaseAgent, build_system_prompt
from apps.agents.session_state import (
    ConsultStage,
    SessionState,
    SymptomInfo,
)

logger = logging.getLogger("apps.agents")


def _normalize_dimension_key(key: str) -> str:
    text = (key or "").strip().lower()
    mapping = {
        "cold": "寒热",
        "hot": "寒热",
        "temperature": "寒热",
        "sweat": "汗液",
        "head": "头身",
        "stool": "大便",
        "urine": "小便",
        "diet": "饮食",
        "chest": "胸腹",
        "eye": "耳目",
        "ear": "耳目",
        "thirst": "口渴",
        "history": "旧病",
        "old": "旧病",
    }
    if key in TEN_QUESTIONS:
        return key
    if key in mapping:
        return mapping[key]
    for cn in TEN_QUESTIONS.keys():
        if cn in key:
            return cn
    return key


def _extract_non_question_text(text: str) -> str:
    """去除编号追问行，仅保留普通文本（用于澄清消息识别）"""
    if not text:
        return ''
    lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
    kept: List[str] = []
    for line in lines:
        normalized = re.sub(r"^\s*\d+[\.、]\s*", "", line)
        if normalized.endswith('？') or '请问' in normalized:
            continue
        kept.append(normalized)
    return ' '.join(kept).strip()

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

任务：
1) 根据已知信息选择最缺失维度追问。
2) 一次最多2问，问题必须是面向患者的疑问句。
3) 信息充分则 is_sufficient=true。
4) 提取新症状。

【重要约束】
1. 绝对不要追问舌象、脉象等专业诊察内容，这些由系统自动处理
2. 如果系统已经提供了舌象分析结果，请直接使用，不要再追问
3. 只追问患者能够直观回答的问题（如感觉、症状、生活习惯等）
4. 问题必须是可以直接问患者的话，禁止输出推理过程
5. 【关键】questions 数组中的每个问题必须是完整的疑问句，如"您怕冷还是怕热？"，禁止类似"需明确患者是否怕冷"的描述性文字

【问题格式示例】
✅ 正确：
- "您怕冷还是怕热？"
- "头疼是胀痛、刺痛还是其他性质？"
- "您容易出汗吗？"

❌ 错误（禁止）：
- "需明确患者是否怕冷"
- "需了解头疼的具体性质"
- "辨别寒热属性"

【舌象自动处理】
- 如果用户上传了舌象图片，系统会自动分析并提供舌象信息
- 如果需要舌象信息但用户未上传，可以提示"您可以上传舌象照片，系统会自动分析"
- 不要直接追问"舌苔是什么颜色"等专业问题

以 JSON 格式返回：
{
  "questions": ["问题1（如无需追问则为空数组）"],
  "is_sufficient": true/false,
  "new_symptoms": [{"name": "新症状", "duration": null, "severity": null, "onset": null}],
  "answered_dimensions": ["已覆盖维度，如：寒热、汗液"],
  "inquiry_answers": {"维度名": "答案摘要"},
  "need_tongue_image": true/false  // 如果需要舌象信息但未提供，设置为true
}

只输出 JSON，不要包含其他文字。
严禁输出 reasoning、思考过程、解释说明。"""
)


class InquiryAgent(BaseAgent):
    """十问追问 Agent"""

    agent_name = "InquiryAgent"
    stage = ConsultStage.INQUIRY

    # 最少需要覆盖的维度数才能推进到辨证
    MIN_DIMENSIONS_REQUIRED = 4  # 从3增加到4，提高信息采集质量
    
    # 关键维度（必须覆盖）
    CRITICAL_DIMENSIONS = {"寒热", "汗液", "饮食", "大便", "小便"}

    def _execute(self, state: SessionState, **kwargs) -> SessionState:
        new_state = state.model_copy(deep=True)

        # 对非症状/非问诊型输入做澄清，避免机械进入固定追问
        user_reply = self._get_latest_user_message(new_state)
        if (
            self._is_non_medical_reply(user_reply)
            and not new_state.symptoms
            and not new_state.inquiry_answers
            and not new_state.pending_questions
        ):
            new_state.pending_questions = []
            new_state.current_stage = ConsultStage.INQUIRY
            new_state.add_message(
                "assistant",
                "我是中医智能问诊助手，主要用于健康问诊与调理建议。"
                "请告诉我您当前的身体不适，比如：哪里不舒服、持续多久、是否怕冷发热等。",
            )
            return new_state

        # 如果已有待回答的问题，先解析用户的回答
        self._apply_user_reply_to_pending(new_state, user_reply)
        
        # 调试日志：打印解析后的 inquiry_answers
        logger.info(f"[InquiryAgent] 解析后 inquiry_answers: {new_state.inquiry_answers}")
        logger.info(f"[InquiryAgent] 解析后 pending_questions: {new_state.pending_questions}")
        logger.info(f"[InquiryAgent] 解析后 answered_count: {len(new_state.inquiry_answers)}")

        # 构建 LLM 输入
        context_summary = new_state.to_context_summary()
        
        # 构建更详细的已回答信息（包含维度+答案）
        already_answered_lines = []
        for k, v in new_state.inquiry_answers.items():
            already_answered_lines.append(f"  - {k}: {v}")
        already_answered = "\n".join(already_answered_lines) if already_answered_lines else "无"
        
        symptoms_str = ", ".join(s.name for s in new_state.symptoms) or "未明确"

        # 调试日志：打印发送给 LLM 的上下文
        logger.info(f"[InquiryAgent] === 发送给 LLM 的上下文 ===")
        logger.info(f"[InquiryAgent] 已收集的 inquiry_answers: {new_state.inquiry_answers}")
        
        messages = [
            {"role": "system", "content": _INQUIRY_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"【患者主诉】{new_state.chief_complaint or '从用户描述中提取'}\n"
                    f"【已收集症状】{symptoms_str}\n"
                    f"【已回答的十问维度及答案】\n{already_answered}\n"
                    f"【用户最新回答】{(user_reply or '（首次进入问诊）')[:200]}\n"
                    "\n【严格约束】"
                    "1. 绝对不要询问已回答的维度！例如：如果'寒热'已有答案'怕热'，就不要再问'您怕冷还是怕热'"
                    "2. 只询问尚未收集到答案的维度"
                    "3. 如果已有5个以上维度答案充分，is_sufficient=true\n"
                    "请输出JSON：{\"questions\": [问题列表], \"is_sufficient\": true/false}"
                ),
            },
        ]

        raw = self._call_llm(messages, temperature=0.2, max_tokens=512)
        data = self._parse_json_output(raw)
        if not data:
            raise ValueError("InquiryAgent 未获取到可解析的结构化输出")

        # 调试日志：打印 LLM 返回的原始数据
        logger.info(f"[InquiryAgent] 原始返回: {data}")
        if data.get("questions"):
            logger.info(f"[InquiryAgent] 生成的问题: {data['questions']}")

        # 【修复】检查 questions 格式，如果有问题则转换
        questions = data.get("questions", [])
        if questions:
            formatted_questions = []
            for q in questions:
                # 如果问题包含括号说明（寒热偏好（是否怕冷或怕热）），转换为疑问句
                if "（" in q and "）" in q:
                    # 提取括号内容并转换为疑问句
                    bracket_content = q.split("（")[1].split("）")[0]
                    # 简化转换
                    if "是否怕冷" in bracket_content or "怕冷" in bracket_content:
                        formatted_questions.append("您怕冷还是怕热？")
                    elif "疼痛" in bracket_content or "头疼" in bracket_content:
                        formatted_questions.append("头疼是什么性质的疼痛？")
                    else:
                        # 通用转换：去掉括号内容，直接保留主问题
                        main_q = q.split("（")[0].strip()
                        if main_q:
                            formatted_questions.append(main_q + "？")
                elif q and not q.endswith("？") and not q.endswith("?"):
                    formatted_questions.append(q + "？")
                else:
                    formatted_questions.append(q)
            data["questions"] = formatted_questions[:2]
            logger.info(f"[InquiryAgent] 格式化后的问题: {data['questions']}")

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

        # 如果模型回了 reasoning 大段文本但结构不稳，先做软标准化
        if "inquiry_answers" in data and isinstance(data.get("inquiry_answers"), dict):
            normalized_answers: Dict[str, str] = {}
            for k, v in data.get("inquiry_answers", {}).items():
                nk = _normalize_dimension_key(str(k))
                normalized_answers[nk] = str(v)[:300]
            data["inquiry_answers"] = normalized_answers

        if "answered_dimensions" in data and isinstance(data.get("answered_dimensions"), list):
            data["answered_dimensions"] = [
                _normalize_dimension_key(str(x)) for x in data.get("answered_dimensions", [])
            ]

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
        # 防止模型在信息不足时“脑补已回答维度”导致过早推进：
        # 仅允许更新已存在维度，不允许凭空新增维度。
        for k, v in data.get("inquiry_answers", {}).items():
            nk = _normalize_dimension_key(str(k))
            if nk in state.inquiry_answers and v:
                state.inquiry_answers[nk] = str(v)[:300]

        # 设置待追问问题
        questions: List[str] = data.get("questions", [])
        questions = self._deduplicate_questions(state, questions)

        # 判断是否信息充足
        is_sufficient = data.get("is_sufficient", False)
        answered_count = len(state.inquiry_answers)
        
        # 调试日志
        logger.info(f"[InquiryAgent] is_sufficient={is_sufficient}, answered_count={answered_count}, MIN_REQUIRED={self.MIN_DIMENSIONS_REQUIRED}")
        logger.info(f"[InquiryAgent] inquiry_answers={state.inquiry_answers}")
        logger.info(f"[InquiryAgent] pending_questions set to: {questions}")
        
        # 检查是否需要舌象图片
        need_tongue_image = data.get("need_tongue_image", False)

        # 判断是否信息充足
        # 防止“第二轮就直接给结论”：
        # 1) 至少执行过一轮Inquiry（本轮不是首轮）
        # 2) 关键维度达到最低覆盖
        # 3) answered_count 与 is_sufficient 达到阈值
        prior_inquiry_rounds = sum(
            1 for r in state.agent_call_records if r.agent_name == "InquiryAgent"
        )
        critical_covered = len(set(state.inquiry_answers.keys()) & self.CRITICAL_DIMENSIONS)
        is_well_answered = (
            prior_inquiry_rounds >= 1 and (
                answered_count >= 7 or
                (is_sufficient and answered_count >= 5 and critical_covered >= 2)
            )
        )
        
        logger.info(
            "[InquiryAgent] is_well_answered=%s, is_sufficient=%s, answered_count=%s, questions_count=%s, prior_inquiry_rounds=%s, critical_covered=%s",
            is_well_answered,
            is_sufficient,
            answered_count,
            len(questions),
            prior_inquiry_rounds,
            critical_covered,
        )
        
        if is_well_answered:
            # 信息充足，推进
            if state.has_image:
                state.current_stage = ConsultStage.OBSERVATION
            else:
                state.current_stage = ConsultStage.SYNDROME
            state.pending_questions = []
        else:
            # 继续追问
            if not questions:
                questions = self._build_minimum_followup_questions(state)
            
            # 如果需要舌象图片，添加提示
            if need_tongue_image and not state.has_image:
                tongue_hint = "💡 您可以上传舌象照片，系统会自动分析舌诊信息，有助于更准确的辨证。"
                questions.append(tongue_hint)
            
            state.pending_questions = questions
            state.current_stage = ConsultStage.INQUIRY
            if questions:
                # 将追问问题合并为一条助手消息
                combined = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
                state.add_message("assistant", combined)

        return state

    def _apply_user_reply_to_pending(self, state: SessionState, user_reply: str) -> None:
        if not user_reply:
            return
        if not state.pending_questions:
            logger.info(f"[InquiryAgent] 没有待回答的问题，跳过")
            return

        logger.info(f"[InquiryAgent] 用户回答: {user_reply}")
        logger.info(f"[InquiryAgent] 待回答问题: {state.pending_questions}")
        
        for question in state.pending_questions:
            dim = self._infer_dimension_from_question(question)
            logger.info(f"[InquiryAgent] 问题 '{question}' 推断维度: {dim}")
            if dim and user_reply:
                existing = state.inquiry_answers.get(dim)
                if existing:
                    state.inquiry_answers[dim] = f"{existing}；{user_reply}"[:300]
                else:
                    state.inquiry_answers[dim] = user_reply[:300]
                logger.info(f"[InquiryAgent] 存储到 inquiry_answers[{dim}] = {user_reply}")

        for dim in self._infer_dimensions_from_reply(user_reply):
            if dim not in state.inquiry_answers:
                state.inquiry_answers[dim] = user_reply[:300]
                logger.info(f"[InquiryAgent] 从回答中推断维度 {dim} = {user_reply}")

        # 如果当前主诉太短（可能是误输入），用更详细的症状描述更新
        if state.chief_complaint and len(state.chief_complaint) < 5:
            # 收集所有已回答的信息来构建更完整的主诉
            complaint_parts = []
            if "头身" in state.inquiry_answers:
                complaint_parts.append(state.inquiry_answers["头身"])
            if "寒热" in state.inquiry_answers:
                complaint_parts.append(state.inquiry_answers["寒热"])
            if complaint_parts:
                state.chief_complaint = "，".join(complaint_parts)[:500]
                logger.info(f"[InquiryAgent] 更新主诉为: {state.chief_complaint}")

        logger.info(f"[InquiryAgent] 回答后 inquiry_answers: {state.inquiry_answers}")
        state.pending_questions = []

    def _infer_dimensions_from_reply(self, user_reply: str) -> List[str]:
        dim_kws = {
            "寒热": ["怕冷", "畏寒", "发热", "发烧", "体温", "手脚冰冷", "手脚冰凉", "四肢冰冷", "四肢冰凉", "畏冷"],
            "汗液": ["出汗", "盗汗", "自汗", "无汗"],
            "头身": ["头痛", "头疼", "头晕", "身体痛", "酸痛"],
            "大便": ["大便", "便秘", "稀", "拉肚子"],
            "小便": ["小便", "尿", "夜尿", "尿频"],
            "饮食": ["食欲", "吃不下", "胃口", "口味"],
            "胸腹": ["胸", "腹", "肚子", "胀"],
            "耳目": ["耳鸣", "听力", "视力", "眼花"],
            "口渴": ["口渴", "喝水", "冷饮", "热饮"],
            "旧病": ["病史", "慢性", "过敏", "既往"],
        }
        hit = []
        for dim, kws in dim_kws.items():
            if any(k in user_reply for k in kws):
                hit.append(dim)
        return hit

    def _infer_dimension_from_question(self, question: str) -> Optional[str]:
        for dim, q in TEN_QUESTIONS.items():
            if q == question:
                return dim

        keyword_map = {
            "寒热": ["怕冷", "发热", "体温", "寒热"],
            "汗液": ["出汗", "自汗", "盗汗", "无汗"],
            "头身": ["头痛", "头晕", "疼痛", "身体"],
            "大便": ["大便", "便秘", "稀溏"],
            "小便": ["小便", "尿", "夜尿"],
            "饮食": ["食欲", "饮食", "口味", "异味"],
            "胸腹": ["胸", "腹", "胀", "腹痛"],
            "耳目": ["耳鸣", "听力", "视力", "眼"],
            "口渴": ["口渴", "喝水", "冷饮", "热饮"],
            "旧病": ["慢性病", "病史", "过敏史", "既往"],
        }
        for dim, kws in keyword_map.items():
            if any(k in question for k in kws):
                return dim
        return None

    def _deduplicate_questions(self, state: SessionState, questions: List[str]) -> List[str]:
        if not questions:
            return []

        # 【增强】收集所有历史问题（不只是最近10条消息）
        asked_recent: set[str] = set()
        
        # 从所有历史消息中收集问题
        for msg in state.messages:
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content", "") or ""
            pure_text = _extract_non_question_text(content)
            if pure_text and pure_text == content.strip():
                continue
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            for line in lines:
                normalized = re.sub(r"^\s*\d+[\.、]\s*", "", line)
                if normalized.endswith("？") or normalized.endswith("?") or "请问" in normalized:
                    asked_recent.add(self._normalize_question_text(line))

        # 也加入 pending_questions
        for q in state.pending_questions:
            asked_recent.add(self._normalize_question_text(q))

        # 同时检查已覆盖维度，避免重复
        answered_dims = set(state.inquiry_answers.keys())

        filtered: List[str] = []
        for q in questions:
            if not q:
                continue
            q_normalized = self._normalize_question_text(q)
            if q_normalized in asked_recent:
                continue
            # 如果问题已回答过，跳过
            dim = self._infer_dimension_from_question(q)
            if dim and dim in answered_dims:
                continue
            if q not in filtered:
                filtered.append(q)

        if filtered:
            return filtered[:2]

        # 如果没有新问题，检查哪些维度还没回答
        for dim, q in TEN_QUESTIONS.items():
            if dim not in state.inquiry_answers:
                return [q]

        return []

    def _build_minimum_followup_questions(self, state: SessionState) -> List[str]:
        for dim, q in TEN_QUESTIONS.items():
            if dim not in state.inquiry_answers:
                return [q]
        return [
            "请补充一下目前最困扰您的症状（例如疼痛部位、持续时间、是否伴随怕冷发热）。"
        ]

    @staticmethod
    def _normalize_question_text(text: str) -> str:
        if not text:
            return ""
        normalized = re.sub(r"^\s*\d+[\.、]\s*", "", text.strip())
        normalized = normalized.replace("\n", " ")
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    @staticmethod
    def _is_non_medical_reply(user_reply: str) -> bool:
        if not user_reply:
            return False
        text = user_reply.strip().lower()
        if text in {"你好", "您好", "hi", "hello", "你是？", "你是谁", "你是"}:
            # 对纯问候保留澄清；“你是谁”在已有问诊上下文时不应中断问诊。
            return text in {"你好", "您好", "hi", "hello"}
        symptom_kws = [
            "痛", "疼", "冷", "热", "咳", "痰", "发烧", "体温", "头", "腹", "胸", "胃", "恶心",
            "呕", "便", "尿", "睡", "失眠", "乏力", "口渴", "口干", "喝水", "不渴",
            "出汗", "盗汗", "汗", "耳鸣", "眩晕", "胃口", "食欲", "持续", "天", "周", "月",
        ]
        return not any(k in user_reply for k in symptom_kws)
