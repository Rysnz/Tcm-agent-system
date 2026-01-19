# coding=utf-8
"""
Kimi模型提供商实现
"""
from typing import Dict

from apps.model_provider.base_model_provider import (
    IModelProvider, ModelInfo, ModelTypeConst, 
    BaseModelCredential, MaxKBBaseModel, ModelInfoManage, ModelProvideInfo
)


class KimiLLMModelCredential(BaseModelCredential):
    """Kimi模型认证"""
    def is_valid(self, model_type: str, model_name, model: Dict[str, object], 
                 model_params, provider, raise_exception=True):
        """验证Kimi模型认证信息"""
        api_key = model.get('api_key')
        if not api_key:
            if raise_exception:
                raise ValueError('API Key不能为空')
            return False
        return True
    
    def encryption_dict(self, model_info: Dict[str, object]):
        """加密Kimi模型认证信息"""
        if 'api_key' in model_info:
            api_key = model_info['api_key']
            if len(api_key) > 7:
                model_info['api_key'] = f"{api_key[:3]}******{api_key[-4:]}"
        return model_info
    
    def get_model_params_setting_form(self, model_name):
        """获取Kimi模型参数设置表单"""
        return [
            {
                "field_type": "input",
                "name": "api_key",
                "label": "API Key",
                "required": True,
                "placeholder": "请输入Kimi API Key"
            },
            {
                "field_type": "input",
                "name": "model",
                "label": "模型名称",
                "required": True,
                "placeholder": "例如: kimi-pro, kimi-pro-max"
            },
            {
                "field_type": "number",
                "name": "temperature",
                "label": "温度",
                "required": False,
                "default": 0.7,
                "min": 0,
                "max": 1
            }
        ]


class KimiChatModel(MaxKBBaseModel):
    """Kimi聊天模型"""
    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        """创建Kimi聊天模型实例"""
        optional_params = MaxKBBaseModel.filter_optional_params(model_kwargs)
        
        # 提取认证信息
        api_key = model_credential.get('api_key')
        model = model_credential.get('model', model_name)
        temperature = model_credential.get('temperature', 0.7)
        
        # 这里需要根据实际情况实现Kimi模型的创建逻辑
        # 暂时返回None，后续可以根据需要完善
        return None
    
    @staticmethod
    def is_cache_model():
        """是否支持模型缓存"""
        return False


class KimiModelProvider(IModelProvider):
    """Kimi模型提供商"""
    def __init__(self):
        # 初始化模型认证
        self.kimi_credential = KimiLLMModelCredential()
        
        # 构建模型信息
        self.model_info_list = [
            ModelInfo('kimi-pro', 'Kimi Pro', ModelTypeConst.LLM, 
                     self.kimi_credential, KimiChatModel),
            ModelInfo('kimi-pro-max', 'Kimi Pro Max', ModelTypeConst.LLM, 
                     self.kimi_credential, KimiChatModel),
            ModelInfo('kimi-8k', 'Kimi 8K', ModelTypeConst.LLM, 
                     self.kimi_credential, KimiChatModel),
        ]
        
        # 构建模型信息管理器
        self.model_info_manage = ModelInfoManage.builder()
        for model_info in self.model_info_list:
            self.model_info_manage.append_model_info(model_info)
        # 设置默认模型
        self.model_info_manage.append_default_model_info(self.model_info_list[0])
        self.model_info_manage = self.model_info_manage.build()
    
    def get_model_info_manage(self):
        """获取模型信息管理器"""
        return self.model_info_manage
    
    def get_model_provide_info(self):
        """获取模型提供商信息"""
        return ModelProvideInfo(
            provider='kimi',
            name='Kimi',
            icon='kimi'  # 这里可以使用图标名称，前端根据名称渲染图标
        )
