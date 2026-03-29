# coding=utf-8
"""
模型提供商模板，用于快速创建新的模型提供商
"""
from typing import Dict

from apps.model_provider.base_model_provider import (
    IModelProvider, ModelInfo, ModelTypeConst, 
    BaseModelCredential, MaxKBBaseModel, ModelInfoManage, ModelProvideInfo
)


class BaseModelCredentialImpl(BaseModelCredential):
    """基础模型认证实现"""
    def is_valid(self, model_type: str, model_name, model: Dict[str, object], 
                 model_params, provider, raise_exception=True):
        """验证模型认证信息"""
        api_key = model.get('api_key')
        if not api_key and raise_exception:
            raise ValueError('API Key不能为空')
        return bool(api_key)
    
    def encryption_dict(self, model_info: Dict[str, object]):
        """加密模型认证信息"""
        if 'api_key' in model_info:
            api_key = model_info['api_key']
            if len(api_key) > 7:
                model_info['api_key'] = f"{api_key[:3]}******{api_key[-4:]}"
        return model_info
    
    def get_model_params_setting_form(self, model_name):
        """获取模型参数设置表单"""
        return [