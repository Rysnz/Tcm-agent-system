from django.db import models
import uuid
import hashlib
import io
import zipfile
from django.core.files.base import ContentFile


class FileSourceType(models.TextChoices):
    """文件源类型"""
    KNOWLEDGE = "KNOWLEDGE"  # 知识库
    APPLICATION = "APPLICATION"  # 应用
    TOOL = "TOOL"  # 工具
    DOCUMENT = "DOCUMENT"  # 文档
    CHAT = "CHAT"  # 对话
    SYSTEM = "SYSTEM"
    TEMPORARY_30_MINUTE = "TEMPORARY_30_MINUTE"  # 临时30分钟
    TEMPORARY_120_MINUTE = "TEMPORARY_120_MINUTE"  # 临时120分钟
    TEMPORARY_1_DAY = "TEMPORARY_1_DAY"  # 临时1天


class File(models.Model):
    """文件模型"""
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid4, editable=False, verbose_name="主键id")
    file_name = models.CharField(max_length=256, verbose_name="文件名称", default="")
    file_size = models.IntegerField(verbose_name="文件大小", default=0)
    sha256_hash = models.CharField(max_length=64, verbose_name="文件sha256_hash标识", default="")
    source_type = models.CharField(
        verbose_name="资源类型",
        choices=FileSourceType.choices,
        default=FileSourceType.TEMPORARY_120_MINUTE.value,
        db_index=True
    )
    source_id = models.CharField(
        verbose_name="资源id",
        default=FileSourceType.TEMPORARY_120_MINUTE.value,
        db_index=True
    )
    meta = models.JSONField(verbose_name="文件关联数据", default=dict)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        db_table = "file"
        verbose_name = "文件"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return f'{self.file_name}({self.id})'

    def save(self, bytes_data=None, force_insert=False, force_update=False, using=None, update_fields=None):
        """保存文件，支持文件去重和压缩"""
        # 如果没有提供bytes_data，直接调用父类的save方法
        if bytes_data is None:
            return super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

        # 计算文件的SHA256哈希值
        self.sha256_hash = self._get_sha256_hash(bytes_data)
        self.file_size = len(bytes_data)

        # 检查是否已存在相同文件
        existing_file = File.objects.filter(sha256_hash=self.sha256_hash).first()
        if existing_file:
            # 如果文件已存在，只更新元数据
            self.id = existing_file.id
            self.file_name = existing_file.file_name
            self.file_size = existing_file.file_size
            return super().save(force_update=True, update_fields=['meta'])

        # 压缩数据
        compressed_data = self._compress_data(bytes_data)

        # 保存到数据库
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

        # 保存压缩后的数据
        self._save_compressed_data(compressed_data)

    def _get_sha256_hash(self, data):
        """计算数据的SHA256哈希值"""
        return hashlib.sha256(data).hexdigest()

    def _compress_data(self, data, compression_level=9):
        """压缩数据到内存"""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zipinfo = zipfile.ZipInfo(self.file_name)
            zipinfo.compress_type = zipfile.ZIP_DEFLATED
            zip_file.writestr(zipinfo, data, compresslevel=compression_level)
        return buffer.getvalue()

    def _save_compressed_data(self, compressed_data):
        """保存压缩后的数据到文件系统"""
        from django.core.files.storage import default_storage
        from django.conf import settings

        # 生成文件路径
        file_path = f'files/{self.id}/{self.file_name}.zip'

        # 保存文件
        default_storage.save(file_path, ContentFile(compressed_data))

    def get_bytes(self):
        """获取文件的原始字节数据"""
        from django.core.files.storage import default_storage
        from django.conf import settings

        # 生成文件路径
        file_path = f'files/{self.id}/{self.file_name}.zip'

        # 读取文件
        try:
            with default_storage.open(file_path, 'rb') as f:
                compressed_data = f.read()
        except FileNotFoundError:
            return b''

        # 解压数据
        try:
            with zipfile.ZipFile(io.BytesIO(compressed_data)) as zip_file:
                return zip_file.read(self.file_name)
        except Exception:
            # 如果数据不是zip格式，直接返回原始数据
            return compressed_data

    def get_url(self):
        """获取文件的访问URL"""
        from django.conf import settings
        return f'{settings.MEDIA_URL}files/{self.id}/{self.file_name}.zip'


class ChatMessage(models.Model):
    """聊天消息模型"""
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid4, editable=False, verbose_name="主键id")
    session = models.ForeignKey('chat.ChatSession', on_delete=models.CASCADE, verbose_name="会话", related_name='messages')
    role = models.CharField(max_length=20, verbose_name="角色", choices=[('user', 'assistant')], default='user')
    content = models.TextField(verbose_name="内容")
    message_type = models.CharField(max_length=50, verbose_name="消息类型", default='text')
    meta = models.JSONField(verbose_name="元数据", default=dict)
    files = models.JSONField(verbose_name="关联文件", default=list)
    tokens = models.IntegerField(verbose_name="消耗的tokens数", default=0)
    satisfaction = models.IntegerField(verbose_name="用户满意度评分", null=True, blank=True, choices=[(0, '不满意'), (1, '满意')])
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)

    class Meta:
        db_table = "chat_message"
        verbose_name = "聊天消息"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return f'{self.role}: {self.content[:50]}'


class ChatSession(models.Model):
    """聊天会话模型"""
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid4, editable=False, verbose_name="主键id")
    application_id = models.CharField(max_length=128, verbose_name="应用ID")
    user_id = models.CharField(max_length=128, verbose_name="用户ID")
    session_name = models.CharField(max_length=256, verbose_name="会话名称", default='新建对话')
    meta = models.JSONField(verbose_name="元数据", default=dict)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)

    class Meta:
        db_table = "chat_session"
        verbose_name = "聊天会话"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return f'{self.session_name}({self.id})'
