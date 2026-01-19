from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.model_provider.models import ModelConfig
from apps.model_provider.serializers import (
    ModelConfigSerializer, ProviderInfoSerializer,
    ModelTypeSerializer, ModelListSerializer
)
from apps.model_provider.provider_manager import global_provider_manager


class ModelConfigViewSet(viewsets.ModelViewSet):
    """模型配置视图集"""
    queryset = ModelConfig.objects.filter(is_delete=False)
    serializer_class = ModelConfigSerializer
    permission_classes = []
    
    def perform_create(self, serializer):
        """创建模型配置时的处理"""
        serializer.save()
    
    def perform_destroy(self, instance):
        """软删除模型配置"""
        instance.is_delete = True
        instance.save()
    
    @action(detail=False, methods=['get'], url_path='active-list')
    def active_list(self, request):
        """获取激活的模型配置列表"""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ModelProviderView(APIView):
    """模型提供商视图"""
    
    def get(self, request):
        """获取所有模型提供商信息"""
        provider_info_list = global_provider_manager.get_provider_info_list()
        serializer = ProviderInfoSerializer(provider_info_list, many=True)
        return Response(serializer.data)


class ModelTypeView(APIView):
    """模型类型视图"""
    
    def get(self, request):
        """获取所有模型类型"""
        model_types = global_provider_manager.get_model_types()
        serializer = ModelTypeSerializer(model_types, many=True)
        return Response(serializer.data)


class ModelListView(APIView):
    """模型列表视图"""
    
    def get(self, request):
        """根据提供商和模型类型获取模型列表"""
        provider_key = request.query_params.get('provider')
        model_type = request.query_params.get('model_type', 'LLM').upper()  # 转换为大写
        
        if not provider_key:
            return Response({
                'error': 'provider参数不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        provider = global_provider_manager.get_provider(provider_key)
        if not provider:
            return Response({
                'error': f'模型提供商{provider_key}不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        model_list = provider.get_model_list(model_type)
        serializer = ModelListSerializer(model_list, many=True)
        return Response(serializer.data)


class ModelCredentialView(APIView):
    """模型认证视图"""
    
    def post(self, request):
        """验证模型认证信息"""
        provider_key = request.data.get('provider')
        model_type = request.data.get('model_type', 'LLM')
        model_name = request.data.get('model_name')
        credential = request.data.get('credential', {})
        
        if not all([provider_key, model_name]):
            return Response({
                'error': 'provider、model_name参数不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        provider = global_provider_manager.get_provider(provider_key)
        if not provider:
            return Response({
                'error': f'模型提供商{provider_key}不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            is_valid = provider.is_valid_credential(
                model_type, model_name, credential, {}, raise_exception=True
            )
            return Response({'is_valid': is_valid})
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ModelParamsFormView(APIView):
    """模型参数表单视图"""
    
    def get(self, request):
        """获取模型参数设置表单"""
        provider_key = request.query_params.get('provider')
        model_name = request.query_params.get('model_name')
        
        if not all([provider_key, model_name]):
            return Response({
                'error': 'provider、model_name参数不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        provider = global_provider_manager.get_provider(provider_key)
        if not provider:
            return Response({
                'error': f'模型提供商{provider_key}不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # 获取模型类型列表，找到匹配的模型类型
            model_info_manage = provider.get_model_info_manage()
            model_type = None
            for info in model_info_manage.model_list:
                if info.name == model_name:
                    model_type = info.model_type
                    break
            
            if not model_type:
                model_type = 'LLM'  # 默认使用LLM类型
            
            model_credential = provider.get_model_credential(model_type, model_name)
            form_config = model_credential.get_model_params_setting_form(model_name)
            
            # 转换为前端期望的格式
            frontend_form_config = []
            for field in form_config:
                frontend_field = {
                    'key': field['name'],
                    'label': field['label'],
                    'type': 'text' if field['field_type'] == 'input' else 'number',
                    'placeholder': field.get('placeholder', ''),
                    'value': field.get('default', ''),
                    'required': field.get('required', False),
                    'min': field.get('min'),
                    'max': field.get('max')
                }
                frontend_form_config.append(frontend_field)
            
            return Response(frontend_form_config)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)