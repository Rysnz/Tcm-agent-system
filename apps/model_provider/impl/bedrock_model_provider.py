# coding=utf-8
"""
Amazon Bedrock模型提供商简化实现
"""
from typing import Dict
from apps.model_provider.base_model_provider import IModelProvider, ModelProvideInfo, ModelInfo, ModelTypeConst, ModelInfoManage, BaseModelCredential
from django.utils.translation import gettext as _


class BedrockModelProvider(IModelProvider):
    """Amazon Bedrock模型提供商"""
    
    def __init__(self):
        # 创建模型信息管理实例
        self.model_info_manage = ModelInfoManage.builder()
        
        # 简化的凭证配置
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
                        "name": "aws_access_key",
                        "label": _("AWS Access Key"),
                        "field_type": "input",
                        "required": True,
                        "placeholder": _("请输入AWS Access Key")
                    },
                    {
                        "name": "aws_secret_key",
                        "label": _("AWS Secret Key"),
                        "field_type": "input",
                        "required": True,
                        "placeholder": _("请输入AWS Secret Key")
                    },
                    {
                        "name": "aws_region",
                        "label": _("AWS Region"),
                        "field_type": "input",
                        "required": True,
                        "placeholder": _("请输入AWS Region，如us-east-1")
                    }
                ]
        
        simple_credential = SimpleCredential()
        
        # 注册Bedrock模型
        self.model_info_manage.append_model_info_list([
            ModelInfo('anthropic.claude-v2', '', ModelTypeConst.LLM, simple_credential, None),
            ModelInfo('anthropic.claude-3-sonnet-20240229-v1:0', '', ModelTypeConst.LLM, simple_credential, None),
            ModelInfo('amazon.titan-text-express-v1', '', ModelTypeConst.LLM, simple_credential, None),
            ModelInfo('amazon.titan-embed-text-v1', '', ModelTypeConst.EMBEDDING, simple_credential, None),
        ])
        
        # 设置默认模型
        self.model_info_manage.append_default_model_info(
            ModelInfo('anthropic.claude-3-sonnet-20240229-v1:0', '', ModelTypeConst.LLM, simple_credential, None)
        )
        self.model_info_manage.append_default_model_info(
            ModelInfo('amazon.titan-embed-text-v1', '', ModelTypeConst.EMBEDDING, simple_credential, None)
        )
        
        self.model_info_manage = self.model_info_manage.build()
    
    def get_model_info_manage(self):
        """获取模型信息管理器"""
        return self.model_info_manage
    
    def get_model_provide_info(self):
        """获取模型提供商信息"""
        return ModelProvideInfo(
            provider='bedrock',
            name=_('Amazon Bedrock'),
            icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>'
        )
    
    def get_model_type_list(self):
        """获取模型类型列表"""
        return [
            {'key': _type.value.get('message'), 'value': _type.value.get('code')}
            for _type in ModelTypeConst
        ]