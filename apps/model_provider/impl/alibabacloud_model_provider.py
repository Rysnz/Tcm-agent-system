# coding=utf-8
"""
阿里云百炼模型提供商简化实现
"""
from typing import Dict
from apps.model_provider.base_model_provider import IModelProvider, ModelProvideInfo, ModelInfo, ModelTypeConst, ModelInfoManage, BaseModelCredential
from django.utils.translation import gettext as _


class AlibabaCloudModelProvider(IModelProvider):
    """阿里云百炼模型提供商"""
    
    def __init__(self):
        # 创建模型信息管理实例
        self.model_info_manage = ModelInfoManage.builder()
        
        # 简化的凭证配置（仅包含API Key和Secret Key）
        class SimpleCredential(BaseModelCredential):
            def is_valid(self, model_type: str, model_name, model: Dict[str, object], 
                         model_params, provider, raise_exception=True):
                """验证模型认证信息"""
                return True
            
            def encryption_dict(self, model_info: Dict[str, object]):
                """加密模型认证信息"""
                return model_info
            
            def get_model_params_setting_form(self, model_name):
                """获取模型参数设置表单"""
                return [
                    {
                        "name": "api_key",
                        "label": _("API Key"),
                        "field_type": "input",
                        "required": True,
                        "placeholder": _("请输入阿里云百炼API Key")
                    },
                    {
                        "name": "api_secret",
                        "label": _("API Secret"),
                        "field_type": "input",
                        "required": True,
                        "placeholder": _("请输入阿里云百炼API Secret")
                    }
                ]
        
        simple_credential = SimpleCredential()
        
        # 注册阿里云百炼模型
        self.model_info_manage.append_model_info_list([
            ModelInfo('qwen-plus-v1', '', ModelTypeConst.LLM, simple_credential, None),
            ModelInfo('qwen-turbo-v1', '', ModelTypeConst.LLM, simple_credential, None),
            ModelInfo('text-embedding-v1', '', ModelTypeConst.EMBEDDING, simple_credential, None),
        ])
        
        # 设置默认模型
        self.model_info_manage.append_default_model_info(
            ModelInfo('qwen-plus-v1', '', ModelTypeConst.LLM, simple_credential, None)
        )
        self.model_info_manage.append_default_model_info(
            ModelInfo('text-embedding-v1', '', ModelTypeConst.EMBEDDING, simple_credential, None)
        )
        
        self.model_info_manage = self.model_info_manage.build()
    
    def get_model_info_manage(self):
        """获取模型信息管理器"""
        return self.model_info_manage
    
    def get_model_provide_info(self):
        """获取模型提供商信息"""
        return ModelProvideInfo(
            provider='alibabacloud',
            name=_('阿里云百炼'),
            icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>'
        )
    
    def get_model_type_list(self):
        """获取模型类型列表"""
        return [
            {'key': _type.value.get('message'), 'value': _type.value.get('code')}
            for _type in ModelTypeConst
        ]