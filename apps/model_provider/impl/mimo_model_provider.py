# coding=utf-8
"""
小米MiMo模型提供商实现
"""
from typing import Dict

from apps.model_provider.base_model_provider import (
    IModelProvider, ModelInfo, ModelTypeConst, 
    BaseModelCredential, MaxKBBaseModel, ModelProvideInfo
)


class MIMOModelCredential(BaseModelCredential):
    """MiMo模型认证"""
    def is_valid(self, model_type: str, model_name, model: Dict[str, object], 
                 model_params, provider, raise_exception=True):
        """验证MiMo模型认证信息"""
        api_key = model.get('api_key')
        base_url = model.get('base_url')
        
        if not api_key:
            if raise_exception:
                raise ValueError('API Key不能为空')
            return False
        
        return True
    
    def encryption_dict(self, model_info: Dict[str, object]):
        """加密MiMo模型认证信息"""
        if 'api_key' in model_info:
            api_key = model_info['api_key']
            # 简单加密，只显示前3位和后4位
            if len(api_key) > 7:
                model_info['api_key'] = f"{api_key[:3]}******{api_key[-4:]}"
        return model_info
    
    def get_model_params_setting_form(self, model_name):
        """获取MiMo模型参数设置表单"""
        return [
            {
                "field_type": "input",
                "name": "api_key",
                "label": "API Key",
                "required": True,
                "placeholder": "请输入MiMo API Key"
            },
            {
                "field_type": "input",
                "name": "base_url",
                "label": "Base URL",
                "required": False,
                "placeholder": "默认: https://api.xiaomimimo.com/v1"
            },
            {
                "field_type": "input",
                "name": "model",
                "label": "模型名称",
                "required": True,
                "placeholder": "例如: mimo-v2-flash, mimo-v2"
            },
            {
                "field_type": "input",
                "name": "temperature",
                "label": "温度",
                "required": False,
                "placeholder": "默认: 0.3",
                "type": "number",
                "min": 0,
                "max": 1.5
            },
            {
                "field_type": "select",
                "name": "frequency_penalty",
                "label": "频率惩罚",
                "required": False,
                "placeholder": "默认: 0",
                "options": [
                    {"label": "0", "value": 0},
                    {"label": "0.5", "value": 0.5},
                    {"label": "1.0", "value": 1.0},
                    {"label": "1.5", "value": 1.5},
                    {"label": "2.0", "value": 2.0}
                ]
            },
            {
                "field_type": "select",
                "name": "presence_penalty",
                "label": "存在惩罚",
                "required": False,
                "placeholder": "默认: 0",
                "options": [
                    {"label": "0", "value": 0},
                    {"label": "0.5", "value": 0.5},
                    {"label": "1.0", "value": 1.0},
                    {"label": "1.5", "value": 1.5},
                    {"label": "2.0", "value": 2.0}
                ]
            },
            {
                "field_type": "select",
                "name": "thinking.type",
                "label": "思维链",
                "required": False,
                "placeholder": "默认: disabled",
                "options": [
                    {"label": "禁用", "value": "disabled"},
                    {"label": "启用", "value": "enabled"}
                ]
            }
        ]


class MIMOChatModel(MaxKBBaseModel):
    """MiMo聊天模型"""
    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        """创建MiMo聊天模型实例"""
        from langchain_openai import ChatOpenAI
        
        optional_params = MaxKBBaseModel.filter_optional_params(model_kwargs)
        
        # 提取认证信息
        api_key = model_credential.get('api_key')
        base_url = model_credential.get('base_url', 'https://api.xiaomimimo.com/v1')
        model = model_credential.get('model', model_name)
        temperature = model_credential.get('temperature', 0.3)
        
        # 构建MiMo特定的参数，注意不要直接传递thinking参数给ChatOpenAI
        # MiMo API使用thinking参数，但ChatOpenAI封装可能不支持
        # 我们应该使用extra_body来传递MiMo特定的参数
        extra_params = {}
        
        # 处理MiMo特定参数
        if 'thinking' in optional_params:
            # 将thinking参数放入extra_body
            extra_params['thinking'] = optional_params.pop('thinking')
        
        # 其他MiMo特定参数
        if 'frequency_penalty' in optional_params:
            extra_params['frequency_penalty'] = optional_params.pop('frequency_penalty')
        
        if 'presence_penalty' in optional_params:
            extra_params['presence_penalty'] = optional_params.pop('presence_penalty')
        
        # 如果有extra_params，放入extra_body
        if extra_params:
            optional_params['extra_body'] = extra_params
        
        # 创建并返回ChatOpenAI实例，使用MiMo API
        chat_mimo = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            **optional_params
        )
        
        return chat_mimo
    
    @staticmethod
    def is_cache_model():
        """是否支持模型缓存"""
        return False


class MIMOModelProvider(IModelProvider):
    """MiMo模型提供商"""
    def __init__(self):
        # 初始化模型认证
        self.mimo_credential = MIMOModelCredential()
        
        # 构建模型信息
        self.model_info_list = [
            ModelInfo('mimo-v2-flash', 'MiMo V2 Flash', ModelTypeConst.LLM, 
                     self.mimo_credential, MIMOChatModel),
            ModelInfo('mimo-v2', 'MiMo V2', ModelTypeConst.LLM, 
                     self.mimo_credential, MIMOChatModel),
        ]
        
        # 构建模型信息管理器
        from apps.model_provider.base_model_provider import ModelInfoManage
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
            provider='mimo',
            name='小米MiMo',
            icon='mimo'  # 这里可以使用图标名称，前端根据名称渲染图标
        )
