from django.db import models
from apps.common.models import BaseModel
from django.contrib.postgres.search import SearchVectorField
import uuid


class VectorField(models.Field):
    def __init__(self, dimension=768, *args, **kwargs):
        self.dimension = dimension
        super().__init__(*args, **kwargs)
    
    def db_type(self, connection):
        return f'vector({self.dimension})'


class Embedding(BaseModel):
    id = models.CharField(max_length=128, primary_key=True, verbose_name="主键id")
    source_id = models.CharField(max_length=128, verbose_name="资源id", db_index=True)
    source_type = models.CharField(verbose_name='资源类型', max_length=20, db_index=True)
    is_active = models.BooleanField(verbose_name="是否可用", max_length=1, default=True)
    knowledge = models.ForeignKey('KnowledgeBase', on_delete=models.DO_NOTHING, verbose_name="知识库关联", db_constraint=False)
    document = models.ForeignKey('Document', on_delete=models.DO_NOTHING, verbose_name="文档关联", db_constraint=False)
    paragraph = models.ForeignKey('Paragraph', on_delete=models.DO_NOTHING, verbose_name="段落关联", db_constraint=False)
    embedding = VectorField(verbose_name="向量")
    search_vector = SearchVectorField(verbose_name="分词", default="")
    meta = models.JSONField(verbose_name="元数据", default=dict)

    class Meta:
        db_table = "tcm_embedding"
        verbose_name = '嵌入'
        verbose_name_plural = verbose_name

class KnowledgeBase(BaseModel):
    name = models.CharField(max_length=128, verbose_name='知识库名称')
    desc = models.TextField(verbose_name='知识库描述', null=True, blank=True)
    meta = models.JSONField(verbose_name='元数据', default=dict, null=True, blank=True)
    user_id = models.UUIDField(verbose_name='用户ID', null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    
    # 检索相关设置
    embedding_model = models.CharField(max_length=128, default='shibing624/text2vec-base-chinese', verbose_name='嵌入模型')
    embedding_dimension = models.IntegerField(default=768, verbose_name='向量维度')
    similarity_threshold = models.FloatField(default=0.5, verbose_name='相似度阈值')
    search_type = models.CharField(max_length=16, default='blend', choices=[
        ('embedding', '向量搜索'),
        ('keywords', '关键词搜索'),
        ('blend', '混合搜索')
    ], verbose_name='搜索模式')
    top_k = models.IntegerField(default=5, verbose_name='返回结果数量')

    class Meta:
        db_table = 'tcm_knowledge_base'
        verbose_name = '知识库'
        verbose_name_plural = verbose_name

class Document(BaseModel):
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, verbose_name='知识库')
    name = models.CharField(max_length=255, verbose_name='文档名称')
    file_type = models.CharField(max_length=32, verbose_name='文件类型')
    file_size = models.BigIntegerField(verbose_name='文件大小')
    file_path = models.CharField(max_length=512, verbose_name='文件路径')
    char_count = models.IntegerField(default=0, verbose_name='字符数')
    paragraph_count = models.IntegerField(default=0, verbose_name='段落数')
    status = models.CharField(max_length=32, default='processing', verbose_name='处理状态')
    progress = models.IntegerField(default=0, verbose_name='处理进度(0-100)')
    meta = models.JSONField(verbose_name='元数据', default=dict, null=True, blank=True)

    class Meta:
        db_table = 'tcm_document'
        verbose_name = '文档'
        verbose_name_plural = verbose_name

class Paragraph(BaseModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, verbose_name='文档')
    content = models.TextField(verbose_name='段落内容')
    title = models.CharField(max_length=255, verbose_name='标题', null=True, blank=True)
    page_number = models.IntegerField(verbose_name='页码', null=True, blank=True)
    meta = models.JSONField(verbose_name='元数据', default=dict, null=True, blank=True)

    class Meta:
        db_table = 'tcm_paragraph'
        verbose_name = '段落'
        verbose_name_plural = verbose_name
