# coding=utf-8
"""
通义千问模型提供商实现
"""
from typing import List, Dict, Any

from apps.model_provider.base_model_provider import (
    IModelProvider, ModelInfo, ModelTypeConst, 
    BaseModelCredential, MaxKBBaseModel, ModelInfoManage, ModelProvideInfo
)


class QWenLLMModelCredential(BaseModelCredential):
    """通义千问LLM凭证"""
    
    def is_valid(self, model_type: str, model_name, model: Dict[str, object], 
                 model_params, provider, raise_exception=True):
        """验证通义千问模型认证信息"""
        api_key = model.get('api_key')
        if not api_key:
            if raise_exception:
                raise ValueError('API Key不能为空')
            return False
        return True
    
    def encryption_dict(self, model_info: Dict[str, object]):
        """加密模型认证信息"""
        return model_info
    
    def get_model_params_setting_form(self, model_name):
        """获取模型参数设置表单"""
        return [
            {
                "name": "api_key",
                "label": "API Key",
                "field_type": "input",
                "required": True,
                "placeholder": "请输入通义千问API Key"
            },
            {
                "name": "base_url",
                "label": "Base URL",
                "field_type": "input",
                "required": False,
                "placeholder": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "default": "https://dashscope.aliyuncs.com/compatible-mode/v1"
            }
        ]


class QWenLLMModel(MaxKBBaseModel):
    """通义千问LLM模型"""
    
    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        """创建模型实例"""
        from langchain_openai import ChatOpenAI
        
        api_key = model_credential.get('api_key')
        base_url = model_credential.get('base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        
        # 过滤可选参数
        optional_params = QWenLLMModel.filter_optional_params(model_kwargs)
        
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            streaming=True,
            **optional_params
        )


class QWenModelProvider(IModelProvider):
    """通义千问模型提供商"""
    
    def __init__(self):
        self.model_info_manage = self._init_model_info_manage()
    
    def _init_model_info_manage(self):
        """初始化模型信息管理器"""
        model_credential = QWenLLMModelCredential()
        
        model_list = [
            ModelInfo(
                name="qwen-turbo",
                desc="通义千问Turbo模型",
                model_type=ModelTypeConst.LLM,
                model_credential=model_credential,
                model_class=QWenLLMModel
            ),
            ModelInfo(
                name="qwen-plus",
                desc="通义千问Plus模型",
                model_type=ModelTypeConst.LLM,
                model_credential=model_credential,
                model_class=QWenLLMModel
            ),
            ModelInfo(
                name="qwen-max",
                desc="通义千问Max模型",
                model_type=ModelTypeConst.LLM,
                model_credential=model_credential,
                model_class=QWenLLMModel
            ),
            ModelInfo(
                name="qwen-max-longcontext",
                desc="通义千问Max长上下文模型",
                model_type=ModelTypeConst.LLM,
                model_credential=model_credential,
                model_class=QWenLLMModel
            )
        ]
        
        return ModelInfoManage.builder().append_model_info_list(model_list).build()
    
    def get_model_info_manage(self):
        """获取模型信息管理器"""
        return self.model_info_manage
    
    def get_model_provide_info(self):
        """获取模型提供商信息"""
        return ModelProvideInfo(
            provider="qwen",
            name="通义千问",
            icon=""
        )
