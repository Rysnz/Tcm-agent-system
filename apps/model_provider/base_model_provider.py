# coding=utf-8
"""
模型提供商基础架构，参考MaxKB实现
"""
from abc import ABC, abstractmethod
from enum import Enum
from functools import reduce
from typing import Dict, Iterator, Type, List

from pydantic import BaseModel
from django.utils.translation import gettext_lazy as _


class ModelTypeConst(Enum):
    """模型类型枚举"""
    LLM = {'code': 'LLM', 'message': _('大语言模型')}
    EMBEDDING = {'code': 'EMBEDDING', 'message': _('嵌入模型')}
    IMAGE = {'code': 'IMAGE', 'message': _('视觉模型')}
    STT = {'code': 'STT', 'message': _('语音转文本')}
    TTS = {'code': 'TTS', 'message': _('文本转语音')}
    TTI = {'code': 'TTI', 'message': _('文本生成图像')}
    RERANKER = {'code': 'RERANKER', 'message': _('重排序模型')}


class ModelProvideInfo:
    """模型提供商信息"""
    def __init__(self, provider: str, name: str, icon: str):
        self.provider = provider
        self.name = name
        self.icon = icon

    def to_dict(self):
        return {
            attr: getattr(self, attr)
            for attr in vars(self)
            if not attr.startswith("__")
        }


class ModelInfo:
    """模型信息"""
    def __init__(self, name: str, desc: str, model_type: ModelTypeConst, 
                 model_credential: 'BaseModelCredential', 
                 model_class: Type['MaxKBBaseModel'],
                 **keywords):
        self.name = name
        self.desc = desc
        self.model_type = model_type.name
        self.model_credential = model_credential
        self.model_class = model_class
        
        # 添加额外关键字参数
        if keywords:
            for key, value in keywords.items():
                setattr(self, key, value)

    def to_dict(self):
        return reduce(
            lambda x, y: {**x, **y},
            [{attr: getattr(self, attr)} for attr in vars(self) 
             if not attr.startswith("__") 
             and attr not in ['model_credential', 'model_class']],
            {}
        )


class ModelInfoManage:
    """模型信息管理器"""
    def __init__(self):
        self.model_dict = {}
        self.model_list = []
        self.default_model_list = []
        self.default_model_dict = {}

    def append_model_info(self, model_info: ModelInfo):
        """添加模型信息"""
        self.model_list.append(model_info)
        model_type_dict = self.model_dict.get(model_info.model_type)
        if model_type_dict is None:
            self.model_dict[model_info.model_type] = {model_info.name: model_info}
        else:
            model_type_dict[model_info.name] = model_info

    def append_default_model_info(self, model_info: ModelInfo):
        """添加默认模型信息"""
        self.default_model_list.append(model_info)
        self.default_model_dict[model_info.model_type] = model_info

    def get_model_list(self):
        """获取所有模型列表"""
        return [model.to_dict() for model in self.model_list]

    def get_model_list_by_model_type(self, model_type):
        """根据模型类型获取模型列表"""
        return [model.to_dict() for model in self.model_list 
                if model.model_type == model_type]

    def get_model_type_list(self):
        """获取模型类型列表"""
        return [
            {'key': _type.value.get('message'), 'value': _type.value.get('code')}
            for _type in ModelTypeConst
        ]

    def get_model_info(self, model_type, model_name) -> ModelInfo:
        """获取模型信息"""
        model_info = self.model_dict.get(model_type, {}).get(
            model_name, self.default_model_dict.get(model_type)
        )
        if model_info is None:
            raise ValueError(f'不支持的模型: {model_type}::{model_name}')
        return model_info

    class builder:
        """构建器模式"""
        def __init__(self):
            self.model_info_manage = ModelInfoManage()

        def append_model_info(self, model_info: ModelInfo):
            """添加模型信息"""
            self.model_info_manage.append_model_info(model_info)
            return self

        def append_model_info_list(self, model_info_list: List[ModelInfo]):
            """批量添加模型信息"""
            for model_info in model_info_list:
                self.model_info_manage.append_model_info(model_info)
            return self

        def append_default_model_info(self, model_info: ModelInfo):
            """添加默认模型信息"""
            self.model_info_manage.append_default_model_info(model_info)
            return self

        def build(self):
            """构建完成"""
            return self.model_info_manage


class MaxKBBaseModel(ABC):
    """模型基类"""
    @staticmethod
    @abstractmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        """创建模型实例"""
        pass

    @staticmethod
    def is_cache_model():
        """是否支持模型缓存"""
        return True

    @staticmethod
    def filter_optional_params(model_kwargs):
        """过滤可选参数"""
        optional_params = {}
        for key, value in model_kwargs.items():
            if key not in ['model_id', 'use_local', 'streaming', 'show_ref_label', 'stream']:
                if key == 'extra_body' and isinstance(value, dict):
                    optional_params.update(value)
                else:
                    optional_params[key] = value
        return optional_params


class BaseModelCredential(ABC):
    """模型认证基类"""
    @abstractmethod
    def is_valid(self, model_type: str, model_name, model: Dict[str, object], 
                 model_params, provider, raise_exception=True):
        """验证模型认证信息"""
        pass

    @abstractmethod
    def encryption_dict(self, model_info: Dict[str, object]):
        """加密模型认证信息"""
        pass

    def get_model_params_setting_form(self, model_name):
        """获取模型参数设置表单"""
        return []


class IModelProvider(ABC):
    """模型提供商接口"""
    @abstractmethod
    def get_model_info_manage(self):
        """获取模型信息管理器"""
        pass

    @abstractmethod
    def get_model_provide_info(self):
        """获取模型提供商信息"""
        pass

    def get_model_type_list(self):
        """获取模型类型列表"""
        return self.get_model_info_manage().get_model_type_list()

    def get_model_list(self, model_type):
        """根据模型类型获取模型列表"""
        if model_type is None:
            raise ValueError('模型类型不能为空')
        return self.get_model_info_manage().get_model_list_by_model_type(model_type)

    def get_model_credential(self, model_type, model_name):
        """获取模型认证信息"""
        model_info = self.get_model_info_manage().get_model_info(model_type, model_name)
        return model_info.model_credential

    def is_valid_credential(self, model_type, model_name, model_credential: Dict[str, object],
                            model_params: Dict[str, object], raise_exception=False):
        """验证模型认证信息"""
        model_info = self.get_model_info_manage().get_model_info(model_type, model_name)
        return model_info.model_credential.is_valid(
            model_type, model_name, model_credential, model_params, self,
            raise_exception=raise_exception
        )

    def get_model(self, model_type, model_name, model_credential: Dict[str, object], **model_kwargs) -> BaseModel:
        """获取模型实例"""
        model_info = self.get_model_info_manage().get_model_info(model_type, model_name)
        return model_info.model_class.new_instance(
            model_type, model_name, model_credential, **model_kwargs
        )
