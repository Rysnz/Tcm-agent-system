# coding=utf-8
"""
智谱AI模型提供商实现
"""
from typing import List, Dict, Any

from apps.model_provider.base_model_provider import (
    IModelProvider, ModelInfo, ModelTypeConst, 
    BaseModelCredential, MaxKBBaseModel, ModelInfoManage, ModelProvideInfo
)


class ZhiPuLLMModelCredential(BaseModelCredential):
    """智谱AI LLM凭证"""
    
    def is_valid(self, model_type: str, model_name, model: Dict[str, object], 
                 model_params, provider, raise_exception=True):
        """验证智谱AI模型认证信息"""
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
                "placeholder": "请输入智谱AI API Key"
            },
            {
                "name": "base_url",
                "label": "Base URL",
                "field_type": "input",
                "required": False,
                "placeholder": "https://open.bigmodel.cn/api/paas/v4",
                "default": "https://open.bigmodel.cn/api/paas/v4"
            }
        ]


class ZhiPuLLMModel(MaxKBBaseModel):
    """智谱AI LLM模型"""
    
    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        """创建模型实例"""
        # 使用智谱AI的LangChain集成
        from langchain_community.chat_models import ChatZhipuAI
        
        api_key = model_credential.get('api_key')
        base_url = model_credential.get('base_url', 'https://open.bigmodel.cn/api/paas/v4')
        
        # 过滤可选参数
        optional_params = ZhiPuLLMModel.filter_optional_params(model_kwargs)
        
        return ChatZhipuAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            streaming=True,
            **optional_params
        )


class ZhiPuModelProvider(IModelProvider):
    """智谱AI模型提供商"""
    
    def __init__(self):
        self.model_info_manage = self._init_model_info_manage()
    
    def _init_model_info_manage(self):
        """初始化模型信息管理器"""
        model_credential = ZhiPuLLMModelCredential()
        
        model_list = [
            ModelInfo(
                name="glm-4",
                desc="GLM-4模型",
                model_type=ModelTypeConst.LLM,
                model_credential=model_credential,
                model_class=ZhiPuLLMModel
            ),
            ModelInfo(
                name="glm-4-flash",
                desc="GLM-4-Flash模型",
                model_type=ModelTypeConst.LLM,
                model_credential=model_credential,
                model_class=ZhiPuLLMModel
            ),
            ModelInfo(
                name="glm-3-turbo",
                desc="GLM-3-Turbo模型",
                model_type=ModelTypeConst.LLM,
                model_credential=model_credential,
                model_class=ZhiPuLLMModel
            ),
            ModelInfo(
                name="glm-3-turbo-instruct",
                desc="GLM-3-Turbo-Instruct模型",
                model_type=ModelTypeConst.LLM,
                model_credential=model_credential,
                model_class=ZhiPuLLMModel
            )
        ]
        
        return ModelInfoManage.builder().append_model_info_list(model_list).build()
    
    def get_model_info_manage(self):
        """获取模型信息管理器"""
        return self.model_info_manage
    
    def get_model_provide_info(self):
        """获取模型提供商信息"""
        return ModelProvideInfo(
            provider="zhipu",
            name="智谱AI",
            icon=""
        )
