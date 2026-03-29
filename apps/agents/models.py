"""
Agent会话持久化模型

用于存储问诊会话状态，支持：
- 会话状态持久化到数据库
- 会话历史查询
- 会话清理和归档
"""
import uuid
from django.db import models
from django.utils import timezone


class ConsultationSession(models.Model):
    """
    问诊会话模型
    
    存储完整的会话状态，支持序列化和反序列化。
    """
    
    # 会话标识
    session_id = models.CharField(
        max_length=64,
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        verbose_name="会话ID"
    )
    
    # 会话状态（JSON格式存储）
    state_data = models.JSONField(
        default=dict,
        verbose_name="会话状态数据",
        help_text="存储完整的SessionState序列化数据"
    )
    
    # 会话元数据
    current_stage = models.CharField(
        max_length=32,
        default="intake",
        verbose_name="当前阶段",
        help_text="问诊流程当前阶段"
    )
    
    is_high_risk = models.BooleanField(
        default=False,
        verbose_name="是否高风险",
        help_text="标记是否检测到高风险症状"
    )
    
    chief_complaint = models.TextField(
        blank=True,
        default="",
        verbose_name="主诉",
        help_text="患者主要不适描述"
    )
    
    primary_syndrome = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name="主证型",
        help_text="辨证结果的主证型"
    )
    
    # 患者信息摘要
    patient_age_group = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="年龄段"
    )
    
    patient_gender = models.CharField(
        max_length=16,
        blank=True,
        default="",
        verbose_name="性别"
    )
    
    is_pregnant = models.BooleanField(
        default=False,
        verbose_name="是否妊娠期"
    )
    
    is_minor = models.BooleanField(
        default=False,
        verbose_name="是否未成年"
    )
    
    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )
    
    last_active_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="最后活跃时间",
        help_text="用于会话超时清理"
    )
    
    # 会话状态
    is_completed = models.BooleanField(
        default=False,
        verbose_name="是否已完成",
        help_text="问诊流程是否已完成"
    )
    
    is_archived = models.BooleanField(
        default=False,
        verbose_name="是否已归档",
        help_text="用于会话归档管理"
    )
    
    # 统计信息
    message_count = models.IntegerField(
        default=0,
        verbose_name="消息数量"
    )
    
    agent_step_count = models.IntegerField(
        default=0,
        verbose_name="Agent执行步数"
    )
    
    # 用户标识（可选，支持匿名和登录用户）
    user_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
        verbose_name="用户ID",
        help_text="关联的用户标识，匿名用户为空"
    )
    
    # 客户端信息
    client_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="客户端IP"
    )
    
    user_agent = models.TextField(
        blank=True,
        default="",
        verbose_name="User-Agent"
    )
    
    class Meta:
        db_table = 'agents_consultation_session'
        verbose_name = "问诊会话"
        verbose_name_plural = "问诊会话"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at'], name='idx_session_updated'),
            models.Index(fields=['user_id', '-updated_at'], name='idx_session_user'),
            models.Index(fields=['current_stage'], name='idx_session_stage'),
            models.Index(fields=['is_completed', '-updated_at'], name='idx_session_status'),
        ]
    
    def __str__(self):
        return f"会话 {self.session_id[:8]}... ({self.current_stage})"
    
    def update_from_state(self, state):
        """从SessionState对象更新模型字段"""
        self.current_stage = state.current_stage
        self.is_high_risk = state.is_high_risk
        self.chief_complaint = state.chief_complaint[:500]  # 限制长度
        self.primary_syndrome = state.primary_syndrome or ""
        self.patient_age_group = state.patient_profile.age_group or ""
        self.patient_gender = state.patient_profile.gender or ""
        self.is_pregnant = state.patient_profile.is_pregnant
        self.is_minor = state.patient_profile.is_minor
        self.message_count = len(state.messages)
        self.agent_step_count = len(state.agent_call_records)
        self.is_completed = state.current_stage == "done"
        self.last_active_at = timezone.now()
        
        # 更新状态数据
        from apps.agents.orchestrator import TCMOrchestrator
        self.state_data = TCMOrchestrator.serialize_state(state)
    
    @classmethod
    def get_active_sessions(cls, timeout_hours=24):
        """获取活跃会话（未超时）"""
        cutoff = timezone.now() - timezone.timedelta(hours=timeout_hours)
        return cls.objects.filter(
            last_active_at__gte=cutoff,
            is_completed=False,
            is_archived=False
        )
    
    @classmethod
    def cleanup_expired_sessions(cls, timeout_hours=48):
        """清理过期会话"""
        cutoff = timezone.now() - timezone.timedelta(hours=timeout_hours)
        expired = cls.objects.filter(
            last_active_at__lt=cutoff,
            is_completed=False
        )
        count = expired.count()
        expired.update(is_archived=True)
        return count
    
    @classmethod
    def get_statistics(cls):
        """获取会话统计信息"""
        from django.db.models import Count, Q
        stats = cls.objects.aggregate(
            total=Count('session_id'),
            completed=Count('session_id', filter=Q(is_completed=True)),
            high_risk=Count('session_id', filter=Q(is_high_risk=True)),
            today=Count('session_id', filter=Q(created_at__date=timezone.now().date())),
        )
        return stats


class AgentExecutionLog(models.Model):
    """
    Agent执行日志模型
    
    记录每次Agent执行的详细信息，用于调试和分析。
    """
    
    id = models.AutoField(primary_key=True)
    
    session = models.ForeignKey(
        ConsultationSession,
        on_delete=models.CASCADE,
        related_name='execution_logs',
        verbose_name="关联会话"
    )
    
    agent_name = models.CharField(
        max_length=64,
        verbose_name="Agent名称"
    )
    
    stage = models.CharField(
        max_length=32,
        verbose_name="执行阶段"
    )
    
    started_at = models.DateTimeField(
        verbose_name="开始时间"
    )
    
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="结束时间"
    )
    
    success = models.BooleanField(
        default=False,
        verbose_name="是否成功"
    )
    
    error_message = models.TextField(
        blank=True,
        default="",
        verbose_name="错误信息"
    )
    
    retry_count = models.IntegerField(
        default=0,
        verbose_name="重试次数"
    )
    
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="执行时长(毫秒)"
    )
    
    input_summary = models.TextField(
        blank=True,
        default="",
        verbose_name="输入摘要"
    )
    
    output_summary = models.TextField(
        blank=True,
        default="",
        verbose_name="输出摘要"
    )
    
    trace_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="追踪ID"
    )
    
    class Meta:
        db_table = 'agents_execution_log'
        verbose_name = "Agent执行日志"
        verbose_name_plural = "Agent执行日志"
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['session', '-started_at'], name='idx_log_session'),
            models.Index(fields=['agent_name', '-started_at'], name='idx_log_agent'),
            models.Index(fields=['success', '-started_at'], name='idx_log_success'),
        ]
    
    def __str__(self):
        status = "成功" if self.success else "失败"
        return f"{self.agent_name} - {status} ({self.started_at})"
