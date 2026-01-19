# coding=utf-8
"""
模型提供商管理器，用于注册和管理所有模型提供商
"""
from typing import Dict, List
from apps.model_provider.base_model_provider import IModelProvider


class ProviderManager:
    """模型提供商管理器"""
    def __init__(self):
        self.provider_dict: Dict[str, IModelProvider] = {}
        self.provider_list: List[IModelProvider] = []
        
    def register_provider(self, provider: IModelProvider):
        """注册模型提供商"""
        provider_info = provider.get_model_provide_info()
        provider_key = provider_info.provider
        self.provider_dict[provider_key] = provider
        self.provider_list.append(provider)
    
    def get_provider(self, provider_key: str) -> IModelProvider:
        """根据提供商Key获取提供商实例"""
        provider = self.provider_dict.get(provider_key)
        # 如果提供商不存在，重新注册所有提供商
        if not provider:
            print(f"提供商 {provider_key} 不存在，正在重新注册所有提供商...")
            # 清除现有提供商
            self.provider_dict.clear()
            self.provider_list.clear()
            # 重新注册所有提供商
            register_builtin_providers()
            # 再次尝试获取提供商
            provider = self.provider_dict.get(provider_key)
        return provider
    
    def get_all_providers(self) -> List[IModelProvider]:
        """获取所有模型提供商"""
        return self.provider_list
    
    def get_provider_info_list(self) -> List[dict]:
        """获取所有模型提供商信息列表"""
        return [
            provider.get_model_provide_info().to_dict()
            for provider in self.provider_list
        ]
    
    def get_model_types(self) -> List[dict]:
        """获取所有模型类型"""
        model_types = set()
        for provider in self.provider_list:
            for model_type in provider.get_model_type_list():
                model_types.add((model_type['value'], model_type['key']))
        
        return [
            {'value': value, 'key': key}
            for value, key in sorted(model_types, key=lambda x: x[0])
        ]


# 创建全局模型提供商管理器实例
global_provider_manager = ProviderManager()

# 注册内置模型提供商
def register_builtin_providers():
    """注册内置模型提供商"""
    providers_to_register = [
        # (provider_class_name, import_path)
        ("OpenAIModelProvider", "apps.model_provider.impl.openai_model_provider"),
        ("MIMOModelProvider", "apps.model_provider.impl.mimo_model_provider"),
        ("AnthropicModelProvider", "apps.model_provider.impl.anthropic_model_provider_simple"),
        ("GeminiModelProvider", "apps.model_provider.impl.gemini_model_provider"),
        ("DeepSeekModelProvider", "apps.model_provider.impl.deepseek_model_provider"),
        ("KimiModelProvider", "apps.model_provider.impl.kimi_model_provider"),
        ("OllamaModelProvider", "apps.model_provider.impl.ollama_model_provider"),
        ("QWenModelProvider", "apps.model_provider.impl.qwen_model_provider"),
        ("ZhiPuModelProvider", "apps.model_provider.impl.zhipu_model_provider"),
        ("XunFeiModelProvider", "apps.model_provider.impl.xunfei_model_provider"),
        ("AlibabaCloudModelProvider", "apps.model_provider.impl.alibabacloud_model_provider"),
        ("BedrockModelProvider", "apps.model_provider.impl.bedrock_model_provider"),
        ("AzureOpenAIModelProvider", "apps.model_provider.impl.azure_openai_model_provider"),
        ("SiliconFlowModelProvider", "apps.model_provider.impl.siliconflow_model_provider"),
        ("TencentCloudModelProvider", "apps.model_provider.impl.tencentcloud_model_provider"),
        ("VLLMModelProvider", "apps.model_provider.impl.vllm_model_provider"),
        ("VolcEngineModelProvider", "apps.model_provider.impl.volcengine_model_provider"),
        ("XorbitsModelProvider", "apps.model_provider.impl.xorbits_model_provider"),
    ]
    
    for provider_class_name, import_path in providers_to_register:
        try:
            # 动态导入并注册模型提供商
            module = __import__(import_path, fromlist=[provider_class_name])
            provider_class = getattr(module, provider_class_name)
            provider_instance = provider_class()
            global_provider_manager.register_provider(provider_instance)
            print(f"成功注册模型提供商: {provider_class_name}")
        except Exception as e:
            print(f"注册模型提供商失败 {provider_class_name}: {str(e)}")
            continue
    

# 初始化注册所有内置模型提供商
register_builtin_providers()
