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
