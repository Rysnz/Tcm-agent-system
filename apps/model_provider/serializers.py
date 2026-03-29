from rest_framework import serializers
from apps.model_provider.models import ModelConfig, AgentModelConfig


class ModelConfigSerializer(serializers.ModelSerializer):
    """模型配置序列化器"""
    class Meta:
        model = ModelConfig
        fields = '__all__'


class ProviderInfoSerializer(serializers.Serializer):
    """模型提供商信息序列化器"""
    provider = serializers.CharField()
    name = serializers.CharField()
    icon = serializers.CharField()


class ModelTypeSerializer(serializers.Serializer):
    """模型类型序列化器"""
    key = serializers.CharField()
    value = serializers.CharField()


class ModelListSerializer(serializers.Serializer):
    """模型列表序列化器"""
    value = serializers.CharField(source='name')
    label = serializers.CharField(source='desc')


class ModelCredentialSerializer(serializers.Serializer):
    """模型认证序列化器"""
    api_key = serializers.CharField(required=True, label='API Key')
    base_url = serializers.CharField(required=False, label='Base URL')
    model = serializers.CharField(required=True, label='模型名称')
    temperature = serializers.FloatField(required=False, default=0.7, label='温度')


class AgentModelConfigSerializer(serializers.ModelSerializer):
    """Agent模型配置序列化器"""

    model_name = serializers.SerializerMethodField()

    class Meta:
        model = AgentModelConfig
        fields = ['id', 'agent_name', 'model', 'model_name', 'create_time', 'update_time']

    @staticmethod
    def get_model_name(obj):
        if obj.model:
            return obj.model.name
        return None
