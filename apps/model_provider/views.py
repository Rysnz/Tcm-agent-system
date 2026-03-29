from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.model_provider.models import ModelConfig, AgentModelConfig
from apps.model_provider.serializers import (
    ModelConfigSerializer, ProviderInfoSerializer,
    ModelTypeSerializer, ModelListSerializer, AgentModelConfigSerializer
)
from apps.model_provider.provider_manager import global_provider_manager
from apps.common.permissions import IsStaffUser
import requests
from apps.model_provider.impl.lmstudio_model_provider import _normalize_lmstudio_base_url


def _resolve_model_credential_handler(provider, model_type, model_name):
    """解析模型凭证处理器，兼容自定义模型名回退"""
    try:
        return provider.get_model_credential(model_type, model_name)
    except Exception:
        model_info_manage = provider.get_model_info_manage()
        default_model_info = getattr(model_info_manage, 'default_model_dict', {}).get(model_type)
        if default_model_info is None:
            candidates = [
                info for info in getattr(model_info_manage, 'model_list', [])
                if getattr(info, 'model_type', None) == model_type
            ]
            default_model_info = candidates[0] if candidates else None
        if default_model_info is None:
            raise
        return default_model_info.model_credential


def _is_missing(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ''
    return False


STRICT_LLM_PROBE_PROVIDERS = {
    'openai', 'zhipu', 'qwen', 'deepseek', 'kimi',
    'gemini', 'anthropic', 'siliconflow', 'mimo', 'lmstudio',
}


def _probe_llm_connection(provider, provider_key, model_type, model_name, credential):
    """执行一次最小化在线调用，校验凭证可用性"""
    if (model_type or '').upper() != 'LLM':
        return
    if provider_key not in STRICT_LLM_PROBE_PROVIDERS:
        return

    model_name_resolved = (credential or {}).get('model') or model_name
    model_credential = {
        **(credential or {}),
        'model': model_name_resolved,
        'temperature': 0,
    }

    if not str(model_name_resolved or '').strip():
        raise RuntimeError('模型名称不能为空')

    # 优先按模型名构造，若是自定义模型名则回退到同类型默认/首个模型类构造
    model = None
    try:
        model = provider.get_model('LLM', model_name_resolved, model_credential)
    except Exception:
        model_info_manage = provider.get_model_info_manage()
        model_info = getattr(model_info_manage, 'default_model_dict', {}).get('LLM')
        if model_info is None:
            candidates = [
                info for info in getattr(model_info_manage, 'model_list', [])
                if getattr(info, 'model_type', None) == 'LLM'
            ]
            model_info = candidates[0] if candidates else None
        model_class = getattr(model_info, 'model_class', None) if model_info else None
        if model_class is not None:
            model = model_class.new_instance('LLM', model_name_resolved, model_credential)

    if model is None or not hasattr(model, 'invoke'):
        raise RuntimeError('当前模型实例不支持连接测试（请检查provider实现）')

    # 最小化请求：要求只返回 OK
    probe_prompt = '请仅回复：OK'
    try:
        response = model.invoke(probe_prompt)
    except Exception as exc:
        err_text = str(exc)
        # LM Studio 常见：模型未加载 / 冷启动
        if provider_key == 'lmstudio':
            if 'timeout' in err_text.lower() or 'timed out' in err_text.lower():
                raise RuntimeError('连接测试超时：请确认LM Studio模型已加载完成（可先在LM Studio对话窗口预热一次）')
            if 'Connection error' in err_text or 'Failed to establish a new connection' in err_text:
                raise RuntimeError('连接测试失败：请确认LM Studio Local Server已启动，且Base URL为 http://127.0.0.1:1234/v1')
        raise RuntimeError(f'连接测试失败: {exc}')

    content = getattr(response, 'content', str(response) if response is not None else '')
    if not str(content).strip():
        raise RuntimeError('连接测试失败: 模型返回为空')


class ModelConfigViewSet(viewsets.ModelViewSet):
    """模型配置视图集"""
    queryset = ModelConfig.objects.filter(is_delete=False)  # type: ignore[attr-defined]
    serializer_class = ModelConfigSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    
    def perform_create(self, serializer):
        """创建模型配置时的处理"""
        validated = serializer.validated_data
        if validated.get('provider') == 'lmstudio':
            cred = dict(validated.get('credential') or {})
            cred['base_url'] = _normalize_lmstudio_base_url(str(cred.get('base_url', 'http://localhost:1234/v1')))
            validated['credential'] = cred
        serializer.save()

    def perform_update(self, serializer):
        """更新模型配置时的处理"""
        validated = serializer.validated_data
        if validated.get('provider') == 'lmstudio':
            cred = dict(validated.get('credential') or {})
            cred['base_url'] = _normalize_lmstudio_base_url(str(cred.get('base_url', 'http://localhost:1234/v1')))
            validated['credential'] = cred
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


class AgentModelConfigView(APIView):
    """Agent 模型绑定配置"""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        queryset = AgentModelConfig.objects.filter(is_delete=False).select_related('model')  # type: ignore[attr-defined]
        serializer = AgentModelConfigSerializer(queryset, many=True)
        return Response(serializer.data)

    def put(self, request):
        payload = request.data
        if not isinstance(payload, list):
            return Response({'error': '请求体必须是数组'}, status=status.HTTP_400_BAD_REQUEST)

        valid_agent_names = {
            'IntakeAgent',
            'InquiryAgent',
            'ObservationAgent',
            'SyndromeAgent',
            'RecommendationAgent',
            'SafetyGuardAgent',
            'ReportAgent',
        }

        for item in payload:
            agent_name = item.get('agent_name')
            model_id = item.get('model')
            if agent_name not in valid_agent_names:
                return Response({'error': f'未知Agent: {agent_name}'}, status=status.HTTP_400_BAD_REQUEST)

            model_obj = None
            if model_id:
                try:
                    model_obj = ModelConfig.objects.get(id=model_id, is_delete=False, is_active=True)  # type: ignore[attr-defined]
                except ModelConfig.DoesNotExist:  # type: ignore[attr-defined]
                    return Response({'error': f'模型不存在或未激活: {model_id}'}, status=status.HTTP_400_BAD_REQUEST)

            AgentModelConfig.objects.update_or_create(  # type: ignore[attr-defined]
                agent_name=agent_name,
                defaults={
                    'model': model_obj,
                    'is_delete': False,
                },
            )

        queryset = AgentModelConfig.objects.filter(is_delete=False).select_related('model')  # type: ignore[attr-defined]
        serializer = AgentModelConfigSerializer(queryset, many=True)
        return Response(serializer.data)


class ModelProviderView(APIView):
    """模型提供商视图"""
    permission_classes = [IsAuthenticated, IsStaffUser]
    
    def get(self, request):
        """获取所有模型提供商信息"""
        provider_info_list = global_provider_manager.get_provider_info_list()
        serializer = ProviderInfoSerializer(provider_info_list, many=True)
        return Response(serializer.data)


class ModelTypeView(APIView):
    """模型类型视图"""
    permission_classes = [IsAuthenticated, IsStaffUser]
    
    def get(self, request):
        """获取所有模型类型"""
        model_types = global_provider_manager.get_model_types()
        serializer = ModelTypeSerializer(model_types, many=True)
        return Response(serializer.data)


class ModelListView(APIView):
    """模型列表视图"""
    permission_classes = [IsAuthenticated, IsStaffUser]
    
    def get(self, request):
        """根据提供商和模型类型获取模型列表"""
        provider_key = request.query_params.get('provider')
        model_type = request.query_params.get('model_type', 'LLM').upper()  # 转换为大写
        base_url = request.query_params.get('base_url')
        
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

        # LM Studio 支持从 /v1/models 动态发现
        if provider_key == 'lmstudio' and model_type == 'LLM':
            endpoint = _normalize_lmstudio_base_url(base_url or 'http://localhost:1234/v1').rstrip('/') + '/models'
            try:
                resp = requests.get(endpoint, timeout=5)
                resp.raise_for_status()
                data = resp.json() or {}
                discovered = []
                for item in data.get('data', []):
                    model_id = item.get('id')
                    if model_id:
                        discovered.append({'value': model_id, 'label': model_id})
                if discovered:
                    model_list = discovered
            except Exception:
                # 动态发现失败时回退静态列表
                pass

        serializer = ModelListSerializer(model_list, many=True)
        return Response(serializer.data)


class ModelCredentialView(APIView):
    """模型认证视图"""
    permission_classes = [IsAuthenticated, IsStaffUser]
    
    def post(self, request):
        """验证模型认证信息"""
        provider_key = request.data.get('provider')
        model_type = request.data.get('model_type', 'LLM')
        model_name = request.data.get('model_name')
        credential = request.data.get('credential', {})
        verify_connection = request.data.get('verify_connection', True)

        if provider_key == 'lmstudio':
            credential = {
                **credential,
                'base_url': _normalize_lmstudio_base_url(str(credential.get('base_url', 'http://localhost:1234/v1'))),
            }
        
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
            credential_handler = _resolve_model_credential_handler(provider, model_type, model_name)

            # 先按表单配置做必填项校验，避免某些 provider 的 is_valid 过于宽松
            form_config = credential_handler.get_model_params_setting_form(model_name) or []
            for field in form_config:
                field_name = field.get('name')
                required = bool(field.get('required'))
                if field_name and required and _is_missing(credential.get(field_name)):
                    return Response(
                        {'error': f'{field.get("label") or field_name} 不能为空'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            is_valid = credential_handler.is_valid(
                model_type,
                model_name,
                credential,
                {},
                provider,
                raise_exception=True,
            )

            if is_valid and verify_connection:
                _probe_llm_connection(provider, provider_key, model_type, model_name, credential)

            return Response({'is_valid': is_valid})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ModelParamsFormView(APIView):
    """模型参数表单视图"""
    permission_classes = [IsAuthenticated, IsStaffUser]
    
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
            if model_info_manage is None:
                return Response({'error': '模型提供商未返回模型信息'}, status=status.HTTP_400_BAD_REQUEST)
            model_type = None
            for info in getattr(model_info_manage, 'model_list', []):
                if info.name == model_name:
                    model_type = info.model_type
                    break
            
            if not model_type:
                model_type = 'LLM'  # 默认使用LLM类型

            model_credential = _resolve_model_credential_handler(provider, model_type, model_name)
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
