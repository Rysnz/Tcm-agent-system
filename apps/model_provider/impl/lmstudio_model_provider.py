# coding=utf-8
"""
LM Studio 模型提供商（OpenAI 兼容 API）

参考：
- 基础地址：http://localhost:1234/v1
- 兼容端点：/v1/chat/completions, /v1/embeddings, /v1/models
"""
from typing import Dict
from urllib.parse import urlparse, urlunparse

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from apps.model_provider.base_model_provider import (
    IModelProvider,
    ModelProvideInfo,
    ModelInfo,
    ModelTypeConst,
    ModelInfoManage,
    BaseModelCredential,
    MaxKBBaseModel,
)


class LMStudioLLMModelCredential(BaseModelCredential):
    """LM Studio LLM 凭证"""

    def is_valid(self, model_type: str, model_name, model: Dict[str, object], model_params, provider, raise_exception=True):
        base_url = model.get("base_url")
        if not base_url:
            if raise_exception:
                raise ValueError("Base URL不能为空")
            return False

        selected_model = model.get("model") or model_name
        if not selected_model:
            if raise_exception:
                raise ValueError("模型名称不能为空")
            return False
        return True

    def encryption_dict(self, model_info: Dict[str, object]):
        return model_info

    def get_model_params_setting_form(self, model_name):
        return [
            {
                "field_type": "input",
                "name": "base_url",
                "label": "Base URL",
                "required": True,
                "placeholder": "http://localhost:1234/v1",
                "default": "http://localhost:1234/v1",
            },
            {
                "field_type": "input",
                "name": "api_key",
                "label": "API Key",
                "required": False,
                "placeholder": "可选，默认 lm-studio",
                "default": "lm-studio",
            },
            {
                "field_type": "input",
                "name": "model",
                "label": "模型名称",
                "required": True,
                "placeholder": "填写 LM Studio 中已加载模型的 identifier",
            },
            {
                "field_type": "number",
                "name": "temperature",
                "label": "温度",
                "required": False,
                "default": 0.7,
                "min": 0,
                "max": 1,
            },
        ]


def _normalize_lmstudio_base_url(base_url: str) -> str:
    """规范化 LM Studio OpenAI 兼容 base_url（兼容误填 /api/v1）。"""
    raw = (base_url or "").strip()
    if not raw:
        return "http://localhost:1234/v1"

    parsed = urlparse(raw)
    path = (parsed.path or "").rstrip("/")

    if path.endswith("/api/v1"):
        path = path[:-len("/api/v1")] + "/v1"
    elif path in {"", "/"}:
        path = "/v1"

    return urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment))


class LMStudioEmbeddingModelCredential(BaseModelCredential):
    """LM Studio Embedding 凭证"""

    def is_valid(self, model_type: str, model_name, model: Dict[str, object], model_params, provider, raise_exception=True):
        base_url = model.get("base_url")
        if not base_url:
            if raise_exception:
                raise ValueError("Base URL不能为空")
            return False
        return True

    def encryption_dict(self, model_info: Dict[str, object]):
        return model_info

    def get_model_params_setting_form(self, model_name):
        return [
            {
                "field_type": "input",
                "name": "base_url",
                "label": "Base URL",
                "required": True,
                "placeholder": "http://localhost:1234/v1",
                "default": "http://localhost:1234/v1",
            },
            {
                "field_type": "input",
                "name": "api_key",
                "label": "API Key",
                "required": False,
                "placeholder": "可选，默认 lm-studio",
                "default": "lm-studio",
            },
        ]


class LMStudioChatModel(MaxKBBaseModel):
    """LM Studio 聊天模型"""

    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        optional_params = MaxKBBaseModel.filter_optional_params(model_kwargs)
        # 统一关闭本地模型思维链输出，降低 token 压力
        for key in ["reasoning_content", "enable_thinking", "thinking", "reasoning", "reasoning_effort"]:
            if key in model_credential and key not in optional_params:
                optional_params[key] = model_credential.get(key)
        base_url = _normalize_lmstudio_base_url(str(model_credential.get("base_url", "http://localhost:1234/v1")))
        api_key = model_credential.get("api_key") or "lm-studio"
        model = model_credential.get("model", model_name)
        temperature = model_credential.get("temperature", 0.7)
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            **optional_params,
        )

    @staticmethod
    def is_cache_model():
        return False


class LMStudioEmbeddingModel(MaxKBBaseModel):
    """LM Studio 嵌入模型"""

    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        optional_params = MaxKBBaseModel.filter_optional_params(model_kwargs)
        base_url = _normalize_lmstudio_base_url(str(model_credential.get("base_url", "http://localhost:1234/v1")))
        api_key = model_credential.get("api_key") or "lm-studio"
        return OpenAIEmbeddings(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            **optional_params,
        )

    @staticmethod
    def is_cache_model():
        return False


class LMStudioModelProvider(IModelProvider):
    """LM Studio 模型提供商"""

    def __init__(self):
        llm_credential = LMStudioLLMModelCredential()
        embedding_credential = LMStudioEmbeddingModelCredential()

        model_info_list = [
            ModelInfo("qwen2.5-7b-instruct", "Qwen 2.5 7B Instruct", ModelTypeConst.LLM, llm_credential, LMStudioChatModel),
            ModelInfo("llama-3.1-8b-instruct", "Llama 3.1 8B Instruct", ModelTypeConst.LLM, llm_credential, LMStudioChatModel),
            ModelInfo("mistral-7b-instruct", "Mistral 7B Instruct", ModelTypeConst.LLM, llm_credential, LMStudioChatModel),
            ModelInfo("text-embedding-nomic-embed-text-v1.5", "Nomic Embed Text v1.5", ModelTypeConst.EMBEDDING, embedding_credential, LMStudioEmbeddingModel),
        ]

        self.model_info_manage = ModelInfoManage.builder()
        for model_info in model_info_list:
            self.model_info_manage.append_model_info(model_info)
        self.model_info_manage.append_default_model_info(model_info_list[0])
        self.model_info_manage = self.model_info_manage.build()

    def get_model_info_manage(self):
        return self.model_info_manage

    def get_model_provide_info(self):
        return ModelProvideInfo(
            provider="lmstudio",
            name="LM Studio",
            icon="lmstudio",
        )
