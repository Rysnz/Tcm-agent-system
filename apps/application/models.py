from django.db import models
from django.conf import settings
from apps.common.models import BaseModel

class Application(BaseModel):
    name = models.CharField(max_length=128, verbose_name='应用名称')
    desc = models.TextField(verbose_name='应用描述', null=True, blank=True)
    icon = models.TextField(verbose_name='图标', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户', null=True, blank=True)
    work_flow = models.JSONField(verbose_name='工作流配置', default=dict)
    model_config = models.JSONField(verbose_name='模型配置', default=dict)
    knowledge_bases = models.JSONField(verbose_name='关联知识库', default=list)
    tools = models.JSONField(verbose_name='关联工具', default=list)
    prompt_template = models.TextField(verbose_name='提示词模板', null=True, blank=True)
    system_prompt = models.TextField(verbose_name='系统提示词', null=True, blank=True)
    prompt_template_type = models.CharField(max_length=64, default='DEFAULT', verbose_name='提示词模板类型')
    similarity_threshold = models.FloatField(default=0.5, verbose_name='相似度阈值，低于该值不使用知识库内容')
    top_k = models.IntegerField(default=5, verbose_name='知识库检索返回的最大段落数')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    enable_file_upload = models.BooleanField(default=True, verbose_name='是否启用文件上传功能')

    class Meta:
        db_table = 'tcm_application'
        verbose_name = '应用'
        verbose_name_plural = verbose_name

class WorkflowNode(BaseModel):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, verbose_name='应用')
    node_id = models.CharField(max_length=64, verbose_name='节点ID')
    node_type = models.CharField(max_length=32, verbose_name='节点类型')
    node_data = models.JSONField(verbose_name='节点数据', default=dict)
    position = models.JSONField(verbose_name='位置信息', default=dict)

    class Meta:
        db_table = 'tcm_workflow_node'
        verbose_name = '工作流节点'
        verbose_name_plural = verbose_name

class WorkflowEdge(BaseModel):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, verbose_name='应用')
    source_node = models.CharField(max_length=64, verbose_name='源节点ID')
    target_node = models.CharField(max_length=64, verbose_name='目标节点ID')
    edge_data = models.JSONField(verbose_name='边数据', default=dict)

    class Meta:
        db_table = 'tcm_workflow_edge'
        verbose_name = '工作流边'
        verbose_name_plural = verbose_name
