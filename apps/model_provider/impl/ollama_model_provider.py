# coding=utf-8
"""
Ollama模型提供商实现
"""
from typing import Dict

from apps.model_provider.base_model_provider import (
    IModelProvider, ModelInfo, ModelTypeConst, 
    BaseModelCredential, MaxKBBaseModel, ModelInfoManage, ModelProvideInfo
)


class OllamaLLMModelCredential(BaseModelCredential):
    """Ollama模型认证"""
    def is_valid(self, model_type: str, model_name, model: Dict[str, object], 
                 model_params, provider, raise_exception=True):
        """验证Ollama模型认证信息"""
        # Ollama不需要API Key，只需要模型名称
        return True
    
    def encryption_dict(self, model_info: Dict[str, object]):
        """加密Ollama模型认证信息"""
        # Ollama不需要加密任何信息
        return model_info
    
    def get_model_params_setting_form(self, model_name):
        """获取Ollama模型参数设置表单"""
        return [
            {
                "field_type": "input",
                "name": "base_url",
                "label": "Ollama API地址",
                "required": False,
                "default": "http://localhost:11434",
                "placeholder": "默认: http://localhost:11434"
            },
            {
                "field_type": "input",
                "name": "model",
                "label": "模型名称",
                "required": True,
                "placeholder": "例如: llama3, mistral, gemma"
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


class OllamaChatModel(MaxKBBaseModel):
    """Ollama聊天模型"""
    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        """创建Ollama聊天模型实例"""
        optional_params = MaxKBBaseModel.filter_optional_params(model_kwargs)
        
        # 提取认证信息
        base_url = model_credential.get('base_url', 'http://localhost:11434')
        model = model_credential.get('model', model_name)
        temperature = model_credential.get('temperature', 0.7)
        
        # 这里需要根据实际情况实现Ollama模型的创建逻辑
        # 暂时返回None，后续可以根据需要完善
        return None
    
    @staticmethod
    def is_cache_model():
        """是否支持模型缓存"""
        return False


class OllamaModelProvider(IModelProvider):
    """Ollama模型提供商"""
    def __init__(self):
        # 初始化模型认证
        self.ollama_credential = OllamaLLMModelCredential()
        
        # 构建模型信息
        self.model_info_list = [
            ModelInfo('llama3', 'Llama 3', ModelTypeConst.LLM, 
                     self.ollama_credential, OllamaChatModel),
            ModelInfo('llama3:70b', 'Llama 3 70B', ModelTypeConst.LLM, 
                     self.ollama_credential, OllamaChatModel),
            ModelInfo('mistral', 'Mistral', ModelTypeConst.LLM, 
                     self.ollama_credential, OllamaChatModel),
            ModelInfo('gemma', 'Gemma', ModelTypeConst.LLM, 
                     self.ollama_credential, OllamaChatModel),
            ModelInfo('phi3', 'Phi 3', ModelTypeConst.LLM, 
                     self.ollama_credential, OllamaChatModel),
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
            provider='ollama',
            name='Ollama',
            icon='ollama'  # 这里可以使用图标名称，前端根据名称渲染图标
        )
