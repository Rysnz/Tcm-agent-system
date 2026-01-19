# coding=utf-8
"""
OpenAI兼容模型提供商实现
"""
from typing import Dict

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from apps.model_provider.base_model_provider import (
    IModelProvider, ModelInfo, ModelTypeConst, 
    BaseModelCredential, MaxKBBaseModel, ModelInfoManage, ModelProvideInfo
)


class OpenAILLMModelCredential(BaseModelCredential):
    """OpenAI模型认证"""
    def is_valid(self, model_type: str, model_name, model: Dict[str, object], 
                 model_params, provider, raise_exception=True):
        """验证OpenAI模型认证信息"""
        api_key = model.get('api_key')
        base_url = model.get('base_url')
        
        if not api_key:
            if raise_exception:
                raise ValueError('API Key不能为空')
            return False
        
        return True
    
    def encryption_dict(self, model_info: Dict[str, object]):
        """加密OpenAI模型认证信息"""
        if 'api_key' in model_info:
            api_key = model_info['api_key']
            # 简单加密，只显示前3位和后4位
            if len(api_key) > 7:
                model_info['api_key'] = f"{api_key[:3]}******{api_key[-4:].upper()}"
        return model_info
    
    def get_model_params_setting_form(self, model_name):
        """获取OpenAI模型参数设置表单"""
        return [
            {
                "field_type": "input",
                "name": "api_key",
                "label": "API Key",
                "required": True,
                "placeholder": "请输入OpenAI API Key"
            },
            {
                "field_type": "input",
                "name": "base_url",
                "label": "Base URL",
                "required": False,
                "placeholder": "默认: https://api.openai.com/v1"
            },
            {
                "field_type": "input",
                "name": "model",
                "label": "模型名称",
                "required": True,
                "placeholder": "例如: gpt-4, gpt-3.5-turbo"
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


class OpenAIEmbeddingModelCredential(BaseModelCredential):
    """OpenAI嵌入模型认证"""
    def is_valid(self, model_type: str, model_name, model: Dict[str, object], 
                 model_params, provider, raise_exception=True):
        """验证OpenAI嵌入模型认证信息"""
        api_key = model.get('api_key')
        if not api_key:
            if raise_exception:
                raise ValueError('API Key不能为空')
            return False
        return True
    
    def encryption_dict(self, model_info: Dict[str, object]):
        """加密OpenAI嵌入模型认证信息"""
        if 'api_key' in model_info:
            api_key = model_info['api_key']
            if len(api_key) > 7:
                model_info['api_key'] = f"{api_key[:3]}******{api_key[-4:].upper()}"
        return model_info
    
    def get_model_params_setting_form(self, model_name):
        """获取OpenAI嵌入模型参数设置表单"""
        return [
            {
                "field_type": "input",
                "name": "api_key",
                "label": "API Key",
                "required": True,
                "placeholder": "请输入OpenAI API Key"
            },
            {
                "field_type": "input",
                "name": "base_url",
                "label": "Base URL",
                "required": False,
                "placeholder": "默认: https://api.openai.com/v1"
            }
        ]


class OpenAIChatModel(MaxKBBaseModel):
    """OpenAI聊天模型"""
    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        """创建OpenAI聊天模型实例"""
        optional_params = MaxKBBaseModel.filter_optional_params(model_kwargs)
        
        # 提取认证信息
        api_key = model_credential.get('api_key')
        base_url = model_credential.get('base_url')
        model = model_credential.get('model', model_name)
        temperature = model_credential.get('temperature', 0.7)
        
        # 创建并返回ChatOpenAI实例
        chat_openai = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            **optional_params
        )
        
        return chat_openai
    
    @staticmethod
    def is_cache_model():
        """是否支持模型缓存"""
        return False


class OpenAIEmbeddingModel(MaxKBBaseModel):
    """OpenAI嵌入模型"""
    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        """创建OpenAI嵌入模型实例"""
        optional_params = MaxKBBaseModel.filter_optional_params(model_kwargs)
        
        # 提取认证信息
        api_key = model_credential.get('api_key')
        base_url = model_credential.get('base_url')
        
        # 创建并返回OpenAIEmbeddings实例
        embedding_model = OpenAIEmbeddings(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            **optional_params
        )
        
        return embedding_model
    
    @staticmethod
    def is_cache_model():
        """是否支持模型缓存"""
        return False


class OpenAIModelProvider(IModelProvider):
    """OpenAI模型提供商"""
    def __init__(self):
        # 初始化模型认证
        self.openai_llm_credential = OpenAILLMModelCredential()
        self.openai_embedding_credential = OpenAIEmbeddingModelCredential()
        
        # 构建模型信息
        self.model_info_list = [
            # LLM模型
            ModelInfo('gpt-3.5-turbo', 'GPT-3.5 Turbo', ModelTypeConst.LLM, 
                     self.openai_llm_credential, OpenAIChatModel),
            ModelInfo('gpt-3.5-turbo-0125', 'GPT-3.5 Turbo 0125', ModelTypeConst.LLM, 
                     self.openai_llm_credential, OpenAIChatModel),
            ModelInfo('gpt-3.5-turbo-1106', 'GPT-3.5 Turbo 1106', ModelTypeConst.LLM, 
                     self.openai_llm_credential, OpenAIChatModel),
            ModelInfo('gpt-4', 'GPT-4', ModelTypeConst.LLM, 
                     self.openai_llm_credential, OpenAIChatModel),
            ModelInfo('gpt-4o', 'GPT-4o', ModelTypeConst.LLM, 
                     self.openai_llm_credential, OpenAIChatModel),
            ModelInfo('gpt-4o-mini', 'GPT-4o Mini', ModelTypeConst.LLM, 
                     self.openai_llm_credential, OpenAIChatModel),
            ModelInfo('gpt-4-turbo', 'GPT-4 Turbo', ModelTypeConst.LLM, 
                     self.openai_llm_credential, OpenAIChatModel),
            ModelInfo('gpt-4-turbo-preview', 'GPT-4 Turbo Preview', ModelTypeConst.LLM, 
                     self.openai_llm_credential, OpenAIChatModel),
            # EMBEDDING模型
            ModelInfo('text-embedding-ada-002', 'Text Embedding Ada 002', ModelTypeConst.EMBEDDING, 
                     self.openai_embedding_credential, OpenAIEmbeddingModel),
            ModelInfo('text-embedding-3-small', 'Text Embedding 3 Small', ModelTypeConst.EMBEDDING, 
                     self.openai_embedding_credential, OpenAIEmbeddingModel),
            ModelInfo('text-embedding-3-large', 'Text Embedding 3 Large', ModelTypeConst.EMBEDDING, 
                     self.openai_embedding_credential, OpenAIEmbeddingModel)
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
            provider='openai',
            name='OpenAI',
            icon='openai'  # 这里可以使用图标名称，前端根据名称渲染图标
        )
