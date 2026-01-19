from rest_framework import serializers
from apps.chat.models import ChatSession, ChatMessage, File, FileSourceType
import uuid

class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = '__all__'
        read_only_fields = ['user_id']

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'


class FileUploadSerializer(serializers.Serializer):
    """文件上传序列化器"""
    file = serializers.FileField(required=True, label='文件')
    meta = serializers.JSONField(required=False, allow_null=True)
    source_id = serializers.CharField(
        required=False, 
        allow_null=True, 
        label='资源id', 
        default=FileSourceType.TEMPORARY_120_MINUTE.value
    )
    source_type = serializers.ChoiceField(
        choices=FileSourceType.choices, 
        required=False, 
        allow_null=True, 
        label='资源类型',
        default=FileSourceType.TEMPORARY_120_MINUTE
    )

    def __init__(self, *args, **kwargs):
        # 保存request，用于访问FILES
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def upload(self, with_valid=True):
        """上传文件"""
        if with_valid:
            # 手动将FILES添加到data中，因为Serializer不会自动处理
            if self.request:
                self.initial_data = dict(self.initial_data)
                for key, value in self.request.FILES.items():
                    self.initial_data[key] = value
            self.is_valid(raise_exception=True)
        else:
            # 即使with_valid=False，也需要验证来设置validated_data
            if self.request:
                self.initial_data = dict(self.initial_data)
                for key, value in self.request.FILES.items():
                    self.initial_data[key] = value
            self.is_valid(raise_exception=True)
        
        meta = self.validated_data.get('meta', None)
        if not meta:
            meta = {'debug': True}
        
        file_id = meta.get('file_id', str(uuid.uuid4()))
        file = File(
            id=file_id,
            file_name=self.validated_data['file'].name,
            meta=meta,
            source_id=self.validated_data.get('source_id') or FileSourceType.TEMPORARY_120_MINUTE.value,
            source_type=self.validated_data.get('source_type') or FileSourceType.TEMPORARY_120_MINUTE
        )
        
        # 读取文件内容
        file_content = self.validated_data['file'].read()
        file.save(bytes_data=file_content)
        
        return {
            'file_id': str(file.id),
            'file_name': file.file_name,
            'file_size': file.file_size,
            'url': file.get_url()
        }


class FileGetSerializer(serializers.Serializer):
    """文件获取序列化器"""
    id = serializers.UUIDField(required=True, label='文件ID')
    
    def get(self):
        """获取文件"""
        self.is_valid(raise_exception=True)
        
        file_id = self.data.get('id')
        try:
            file = File.objects.get(id=file_id)
        except File.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('文件不存在')
        
        # 获取文件内容
        file_bytes = file.get_bytes()
        
        return {
            'file_id': str(file.id),
            'file_name': file.file_name,
            'file_size': file.file_size,
            'content': file_bytes,
            'url': file.get_url()
        }
