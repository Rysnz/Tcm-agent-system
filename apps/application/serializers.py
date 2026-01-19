from rest_framework import serializers
from .models import Application, WorkflowNode, WorkflowEdge


class WorkflowNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowNode
        fields = '__all__'


class WorkflowEdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowEdge
        fields = '__all__'


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['id', 'name', 'desc', 'icon', 'work_flow', 'model_config', 'knowledge_bases', 'tools', 'prompt_template', 'system_prompt', 'prompt_template_type', 'similarity_threshold', 'top_k', 'is_active', 'enable_file_upload', 'create_time', 'update_time']
