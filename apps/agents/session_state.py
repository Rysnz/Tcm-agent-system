"""
统一会话状态机 - 在各 Agent 之间传递共享上下文。

设计原则：
- 不可变快照：每次 Agent 执行前后均可序列化为 JSON，方便持久化与链路追踪。
- Pydantic 强类型：确保字段约束与文档一致性。
- 安全优先：high_risk 标志一旦为 True，下游 Agent 必须触发就医建议。
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 枚举定义
# ---------------------------------------------------------------------------

class ConsultStage(str, Enum):
    """问诊流程阶段"""
    INTAKE = "intake"               # 接诊分诊
    INQUIRY = "inquiry"             # 十问追问
    OBSERVATION = "observation"     # 望诊融合
    SYNDROME = "syndrome"           # 辨证分型
    RECOMMENDATION = "recommendation"  # 调理建议
    SAFETY_CHECK = "safety_check"   # 安全审查
    REPORT = "report"               # 报告生成
    DONE = "done"                   # 完成


class ConstitutionType(str, Enum):
    """中医九种体质"""
    BALANCED = "平和质"
    QI_DEFICIENCY = "气虚质"
    YANG_DEFICIENCY = "阳虚质"
    YIN_DEFICIENCY = "阴虚质"
    PHLEGM_DAMPNESS = "痰湿质"
    DAMP_HEAT = "湿热质"
    BLOOD_STASIS = "血瘀质"
    QI_STAGNATION = "气郁质"
    SPECIAL = "特禀质"
    UNKNOWN = "未知"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"   # 立即就医


# ---------------------------------------------------------------------------
# 子模型
# ---------------------------------------------------------------------------

class SymptomInfo(BaseModel):
    """症状信息"""
    name: str = Field(description="症状名称")
    duration: Optional[str] = Field(default=None, description="持续时间，如'3天'")
    severity: Optional[str] = Field(default=None, description="严重程度：轻/中/重")
    onset: Optional[str] = Field(default=None, description="发作方式：急/缓")


class PatientProfile(BaseModel):
    """患者基本信息"""
    age_group: Optional[str] = Field(default=None, description="年龄段：儿童/青年/中年/老年")
    gender: Optional[str] = Field(default=None, description="性别")
    is_pregnant: bool = Field(default=False, description="是否妊娠期")
    is_minor: bool = Field(default=False, description="是否未成年")
    constitution: ConstitutionType = Field(default=ConstitutionType.UNKNOWN, description="体质类型")
    medical_history: List[str] = Field(default_factory=list, description="既往病史")
    allergies: List[str] = Field(default_factory=list, description="过敏史")
    current_medications: List[str] = Field(default_factory=list, description="正在使用的药物")


class ObservationData(BaseModel):
    """望诊数据（文本 + 图像特征）"""
    tongue_color: Optional[str] = Field(default=None, description="舌色：淡白/淡红/红/绛/紫")
    tongue_coating: Optional[str] = Field(default=None, description="苔色：白/黄/灰黑")
    coating_thickness: Optional[str] = Field(default=None, description="苔厚薄：薄/厚")
    coating_texture: Optional[str] = Field(default=None, description="苔质：润/燥/腻/剥")
    tongue_shape: Optional[str] = Field(default=None, description="舌形：正常/胖大/瘦薄/裂纹")
    face_color: Optional[str] = Field(default=None, description="面色：红润/苍白/萎黄/晦暗/青紫")
    image_analysis_raw: Optional[Dict[str, Any]] = Field(default=None, description="图像分析原始结果")
    image_features: List[str] = Field(default_factory=list, description="提取的视觉特征列表")


class SyndromeCandidate(BaseModel):
    """候选证型"""
    name: str = Field(description="证型名称，如'风寒束表证'")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度 0~1")
    supporting_symptoms: List[str] = Field(default_factory=list, description="支持该证型的症状列表")
    evidence_chunks: List[str] = Field(default_factory=list, description="RAG 检索到的支持性文本片段")
    sources: List[str] = Field(default_factory=list, description="知识来源（文档名称等）")


class RecommendationItem(BaseModel):
    """单条调理建议"""
    category: str = Field(description="类别：饮食/作息/运动/情志/穴位/代茶饮")
    content: str = Field(description="具体建议内容（禁止输出处方剂量）")
    rationale: str = Field(default="", description="建议依据（与证型/体质的关联说明）")
    caution: Optional[str] = Field(default=None, description="注意事项")


class SafetyCheckResult(BaseModel):
    """安全审查结果"""
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    triggered_keywords: List[str] = Field(default_factory=list, description="触发的高危关键词")
    special_population_flags: List[str] = Field(default_factory=list, description="特殊人群标记")
    should_refer_immediately: bool = Field(default=False, description="是否建议立即就医")
    safety_message: Optional[str] = Field(default=None, description="安全提示语")
    blocked_content: Optional[str] = Field(default=None, description="被拦截的不当内容（如明确处方剂量）")


class AgentCallRecord(BaseModel):
    """Agent 调用记录，用于链路追踪"""
    agent_name: str
    stage: ConsultStage
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    success: bool = False
    error_msg: Optional[str] = None
    retry_count: int = 0
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None


class ReferenceChunk(BaseModel):
    """RAG 检索到的参考文本片段"""
    content: str = Field(description="文本片段内容")
    source: str = Field(default="", description="来源文档名称")
    score: float = Field(default=0.0, description="相关性得分")
    chunk_id: Optional[str] = None


# ---------------------------------------------------------------------------
# 统一会话状态
# ---------------------------------------------------------------------------

class SessionState(BaseModel):
    """
    统一会话状态 —— 贯穿所有 Agent 的核心数据结构。

    使用说明：
    - 每个 Agent 接收本对象的副本，填充各自负责的字段，返回更新后的副本。
    - orchestrator 负责推进 current_stage 并合并 agent_call_records。
    """

    # 会话标识
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # 流程阶段
    current_stage: ConsultStage = Field(default=ConsultStage.INTAKE)

    # 对话历史（原始用户消息列表）
    messages: List[Dict[str, str]] = Field(
        default_factory=list,
        description="格式：[{'role': 'user'/'assistant', 'content': '...'}]"
    )

    # 患者信息
    patient_profile: PatientProfile = Field(default_factory=PatientProfile)

    # 症状列表（由 IntakeAgent / InquiryAgent 填充）
    chief_complaint: str = Field(default="", description="主诉（患者自述最主要的不适）")
    symptoms: List[SymptomInfo] = Field(default_factory=list)
    inquiry_answers: Dict[str, str] = Field(
        default_factory=dict,
        description="十问答案，key 为问题编号或问题名称"
    )

    # 望诊数据（由 ObservationAgent 填充）
    observation: ObservationData = Field(default_factory=ObservationData)
    has_image: bool = Field(default=False, description="是否上传了舌象/面色图片")

    # 辨证结果（由 SyndromeAgent 填充）
    syndrome_candidates: List[SyndromeCandidate] = Field(default_factory=list)
    primary_syndrome: Optional[str] = Field(default=None, description="最终主证型")

    # 调理建议（由 RecommendationAgent 填充）
    recommendations: List[RecommendationItem] = Field(default_factory=list)

    # 安全审查结果（由 SafetyGuardAgent 填充）
    safety_result: SafetyCheckResult = Field(default_factory=SafetyCheckResult)
    is_high_risk: bool = Field(
        default=False,
        description="高风险标志：一旦为 True，下游 Agent 必须触发就医建议"
    )

    # RAG 参考片段（由各 Agent 检索并累积）
    reference_chunks: List[ReferenceChunk] = Field(default_factory=list)

    # 最终报告
    report_text: Optional[str] = Field(default=None, description="可读版问诊报告")
    report_json: Optional[Dict[str, Any]] = Field(default=None, description="结构化 JSON 报告")

    # 链路追踪
    agent_call_records: List[AgentCallRecord] = Field(default_factory=list)

    # 免责声明（始终附加在最终输出中）
    disclaimer: str = Field(
        default=(
            "⚠️ 重要提示：本系统输出内容仅为健康建议与中医辨证参考，"
            "不构成任何医疗诊断结论，不能替代执业医师的专业诊疗。"
            "如有疑问或症状较重，请及时就医。"
        )
    )

    # 需要继续追问的问题列表（由 InquiryAgent 设置）
    pending_questions: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True

    def add_message(self, role: str, content: str) -> None:
        """添加对话消息"""
        self.messages.append({"role": role, "content": content})
        self.updated_at = datetime.utcnow()

    def add_reference_chunk(self, chunk: ReferenceChunk) -> None:
        """添加 RAG 参考片段（去重）"""
        existing_ids = {c.chunk_id for c in self.reference_chunks if c.chunk_id}
        if chunk.chunk_id and chunk.chunk_id in existing_ids:
            return
        self.reference_chunks.append(chunk)

    def mark_high_risk(self, reason: str) -> None:
        """标记高风险状态"""
        self.is_high_risk = True
        self.safety_result.risk_level = RiskLevel.CRITICAL
        self.safety_result.should_refer_immediately = True
        if not self.safety_result.safety_message:
            self.safety_result.safety_message = reason

    def to_context_summary(self) -> str:
        """生成供 Agent prompt 使用的上下文摘要"""
        lines = [
            f"【主诉】{self.chief_complaint or '未提供'}",
            f"【当前阶段】{self.current_stage}",
        ]
        if self.patient_profile.age_group:
            lines.append(f"【年龄段】{self.patient_profile.age_group}")
        if self.patient_profile.gender:
            lines.append(f"【性别】{self.patient_profile.gender}")
        if self.patient_profile.is_pregnant:
            lines.append("【特殊人群】妊娠期")
        if self.patient_profile.is_minor:
            lines.append("【特殊人群】未成年人")
        if self.symptoms:
            symptom_names = [s.name for s in self.symptoms]
            lines.append(f"【症状列表】{', '.join(symptom_names)}")
        if self.inquiry_answers:
            lines.append("【十问情况】")
            for k, v in self.inquiry_answers.items():
                lines.append(f"  - {k}: {v}")
        if self.observation.tongue_color:
            lines.append(
                f"【舌象】舌色:{self.observation.tongue_color} "
                f"苔色:{self.observation.tongue_coating} "
                f"苔厚:{self.observation.coating_thickness}"
            )
        if self.primary_syndrome:
            lines.append(f"【主证型】{self.primary_syndrome}")
        if self.is_high_risk:
            lines.append("⚠️ 【高风险标志已激活，需立即就医建议】")
        return "\n".join(lines)
