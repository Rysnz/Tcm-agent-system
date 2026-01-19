# coding=utf-8
"""
Anthropic模型提供商实现
"""
import os
from django.conf import settings

from apps.model_provider.base_model_provider import IModelProvider, ModelProvideInfo, ModelInfo, 
    ModelTypeConst, ModelInfoManage
from apps.model_provider.impl.anthropic_model_provider.credential.image import AnthropicImageModelCredential
from apps.model_provider.impl.anthropic_model_provider.credential.llm import AnthropicLLMModelCredential
from apps.model_provider.impl.anthropic_model_provider.model.image import AnthropicImage
from apps.model_provider.impl.anthropic_model_provider.model.llm import AnthropicChatModel

# 获取项目目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

openai_llm_model_credential = AnthropicLLMModelCredential()
openai_image_model_credential = AnthropicImageModelCredential()

model_info_list = [
    ModelInfo('claude-3-opus-20240229', '', ModelTypeConst.LLM,
              openai_llm_model_credential, AnthropicChatModel
              ),
    ModelInfo('claude-3-sonnet-20240229', '', ModelTypeConst.LLM, openai_llm_model_credential,
              AnthropicChatModel),
    ModelInfo('claude-3-haiku-20240307', '', ModelTypeConst.LLM, openai_llm_model_credential,
              AnthropicChatModel),
    ModelInfo('claude-3-5-sonnet-20240620', '', ModelTypeConst.LLM, openai_llm_model_credential,
              AnthropicChatModel),
    ModelInfo('claude-3-5-haiku-20241022', '', ModelTypeConst.LLM, openai_llm_model_credential,
              AnthropicChatModel),
    ModelInfo('claude-3-5-sonnet-20241022', '', ModelTypeConst.LLM, openai_llm_model_credential,
              AnthropicChatModel),
]

image_model_info = [
    ModelInfo('claude-3-5-sonnet-20241022', '', ModelTypeConst.IMAGE, openai_image_model_credential,
              AnthropicImage),
]

model_info_manage = (
    ModelInfoManage.builder()
    .append_model_info_list(model_info_list)
    .append_default_model_info(model_info_list[0])
    .append_model_info_list(image_model_info)
    .append_default_model_info(image_model_info[0])
    .build()
)


class AnthropicModelProvider(IModelProvider):

    def get_model_info_manage(self):
        return model_info_manage

    def get_model_provide_info(self):
        return ModelProvideInfo(provider='model_anthropic_provider', name='Anthropic', icon=get_file_content(
            os.path.join(PROJECT_DIR, "apps", 'models_provider', 'impl', 'anthropic_model_provider', 'icon',
                         'anthropic_icon_svg')))
