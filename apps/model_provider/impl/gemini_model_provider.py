# coding=utf-8
"""
Gemini模型提供商实现
"""
from typing import Dict

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from apps.model_provider.base_model_provider import (
    IModelProvider, ModelInfo, ModelTypeConst, 
    BaseModelCredential, MaxKBBaseModel, ModelInfoManage, ModelProvideInfo
)


class GeminiLLMModelCredential(BaseModelCredential):
    """Gemini模型认证"""
    def is_valid(self, model_type: str, model_name, model: Dict[str, object], 
                 model_params, provider, raise_exception=True):
        """验证Gemini模型认证信息"""
        api_key = model.get('api_key')
        if not api_key:
            if raise_exception:
                raise ValueError('API Key不能为空')
            return False
        return True
    
    def encryption_dict(self, model_info: Dict[str, object]):
        """加密Gemini模型认证信息"""
        if 'api_key' in model_info:
            api_key = model_info['api_key']
            if len(api_key) > 7:
                model_info['api_key'] = f"{api_key[:3]}******{api_key[-4:]}"
        return model_info
    
    def get_model_params_setting_form(self, model_name):
        """获取Gemini模型参数设置表单"""
        return [
            {
                "field_type": "input",
                "name": "api_key",
                "label": "API Key",
                "required": True,
                "placeholder": "请输入Gemini API Key"
            },
            {
                "field_type": "input",
                "name": "model",
                "label": "模型名称",
                "required": True,
                "placeholder": "例如: gemini-pro, gemini-1.5-pro"
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


class GeminiChatModel(MaxKBBaseModel):
    """Gemini聊天模型"""
    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        """创建Gemini聊天模型实例"""
        optional_params = MaxKBBaseModel.filter_optional_params(model_kwargs)
        
        # 提取认证信息
        api_key = model_credential.get('api_key')
        model = model_credential.get('model', model_name)
        temperature = model_credential.get('temperature', 0.7)
        
        # 创建并返回ChatGoogleGenerativeAI实例
        chat_gemini = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
            **optional_params
        )
        
        return chat_gemini
    
    @staticmethod
    def is_cache_model():
        """是否支持模型缓存"""
        return False


class GeminiEmbeddingModel(MaxKBBaseModel):
    """Gemini嵌入模型"""
    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        """创建Gemini嵌入模型实例"""
        optional_params = MaxKBBaseModel.filter_optional_params(model_kwargs)
        
        # 提取认证信息
        api_key = model_credential.get('api_key')
        
        # 创建并返回GoogleGenerativeAIEmbeddings实例
        embedding_model = GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=api_key,
            **optional_params
        )
        
        return embedding_model
    
    @staticmethod
    def is_cache_model():
        """是否支持模型缓存"""
        return False


class GeminiModelProvider(IModelProvider):
    """Gemini模型提供商"""
    def __init__(self):
        # 初始化模型认证
        self.gemini_credential = GeminiLLMModelCredential()
        
        # 构建模型信息
        self.model_info_list = [
            # LLM模型
            ModelInfo('gemini-pro', 'Gemini Pro', ModelTypeConst.LLM, 
                     self.gemini_credential, GeminiChatModel),
            ModelInfo('gemini-1.5-pro', 'Gemini 1.5 Pro', ModelTypeConst.LLM, 
                     self.gemini_credential, GeminiChatModel),
            ModelInfo('gemini-1.5-flash', 'Gemini 1.5 Flash', ModelTypeConst.LLM, 
                     self.gemini_credential, GeminiChatModel),
            ModelInfo('gemini-1.5-pro-001', 'Gemini 1.5 Pro 001', ModelTypeConst.LLM, 
                     self.gemini_credential, GeminiChatModel),
            ModelInfo('gemini-1.5-flash-001', 'Gemini 1.5 Flash 001', ModelTypeConst.LLM, 
                     self.gemini_credential, GeminiChatModel),
            # EMBEDDING模型
            ModelInfo('text-embedding-004', 'Text Embedding 004', ModelTypeConst.EMBEDDING, 
                     self.gemini_credential, GeminiEmbeddingModel),
            ModelInfo('embedding-001', 'Embedding 001', ModelTypeConst.EMBEDDING, 
                     self.gemini_credential, GeminiEmbeddingModel),
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
            provider='gemini',
            name='Gemini',
            icon='gemini'  # 这里可以使用图标名称，前端根据名称渲染图标
        )
