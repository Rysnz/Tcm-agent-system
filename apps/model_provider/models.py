from django.db import models


class ModelConfig(models.Model):
    """模型配置表"""
    # 模型基本信息
    name = models.CharField(max_length=100, verbose_name='模型名称')
    model_type = models.CharField(max_length=50, verbose_name='模型类型', default='LLM')
    provider = models.CharField(max_length=50, verbose_name='模型提供商')
    model_name = models.CharField(max_length=100, verbose_name='模型标识')
    
    # 模型认证信息（加密存储）
    credential = models.JSONField(verbose_name='认证信息')
    
    # 模型参数
    params = models.JSONField(verbose_name='模型参数', default=dict)
    
    # 状态
    is_active = models.BooleanField(verbose_name='是否激活', default=True)
    is_delete = models.BooleanField(verbose_name='是否删除', default=False)
    
    # 时间信息
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '模型配置'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']
    
    def __str__(self):
        return f'{self.name}({self.model_name})'


class AgentModelConfig(models.Model):
    """Agent模型分配配置——为每个智能体指定独立的模型"""
    agent_name = models.CharField(
        max_length=100, unique=True, verbose_name='Agent名称',
        help_text='如：IntakeAgent、InquiryAgent'
    )
    model_config = models.ForeignKey(
        ModelConfig, null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name='分配的模型配置',
        related_name='agent_assignments'
    )
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    class Meta:
        verbose_name = 'Agent模型配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.agent_name} → {self.model_config}'
