import uuid
from django.db import models
from django.contrib.auth.models import User


class BaseModel(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_delete = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        abstract = True


class Application(BaseModel):
    name = models.CharField(max_length=128, verbose_name='应用名称')
    desc = models.TextField(blank=True, null=True, verbose_name='应用描述')
    icon = models.CharField(blank=True, max_length=512, null=True, verbose_name='图标')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户', null=True, blank=True)
    work_flow = models.JSONField(default=dict, verbose_name='工作流配置')
    model_config = models.JSONField(default=dict, verbose_name='模型配置')
    knowledge_bases = models.JSONField(default=list, verbose_name='关联知识库')
    tools = models.JSONField(default=list, verbose_name='关联工具')
    prompt_template = models.TextField(blank=True, null=True, verbose_name='提示词模板')
    prompt_template_type = models.CharField(default='DEFAULT', max_length=64, verbose_name='提示词模板类型')
    similarity_threshold = models.FloatField(default=0.5, verbose_name='相似度阈值，低于该值不使用知识库内容')
    system_prompt = models.TextField(blank=True, null=True, verbose_name='系统提示词')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    top_k = models.IntegerField(default=5, verbose_name='检索返回数量')

    class Meta:
        db_table = 'tcm_application'
        verbose_name = '应用'
        verbose_name_plural = '应用'


class WorkflowNode(BaseModel):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, verbose_name='应用')
    node_id = models.CharField(max_length=64, verbose_name='节点ID')
    node_type = models.CharField(max_length=32, verbose_name='节点类型')
    node_data = models.JSONField(default=dict, verbose_name='节点数据')
    position = models.JSONField(default=dict, verbose_name='位置信息')

    class Meta:
        db_table = 'tcm_workflow_node'
        verbose_name = '工作流节点'
        verbose_name_plural = '工作流节点'


class WorkflowEdge(BaseModel):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, verbose_name='应用')
    source_node = models.CharField(max_length=64, verbose_name='源节点ID')
    target_node = models.CharField(max_length=64, verbose_name='目标节点ID')
    edge_data = models.JSONField(default=dict, verbose_name='边数据')

    class Meta:
        db_table = 'tcm_workflow_edge'
        verbose_name = '工作流边'
        verbose_name_plural = '工作流边'
