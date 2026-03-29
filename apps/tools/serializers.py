from rest_framework import serializers
from apps.tools.models import Tool, MCPTool


class ToolSerializer(serializers.ModelSerializer):
    
    def destroy(self, instance):
        instance.is_delete = True
        instance.save()
    
    class Meta:
        model = Tool
        fields = '__all__'


class MCPToolSerializer(serializers.ModelSerializer):
    
    def destroy(self, instance):
        instance.is_delete = True
        instance.save()
    
    class Meta:
        model = MCPTool
        fields = '__all__'
