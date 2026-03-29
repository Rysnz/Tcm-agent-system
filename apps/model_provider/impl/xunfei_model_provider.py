# coding=utf-8
"""
讯飞星火模型提供商简化实现
"""
from typing import Dict, Any
import io
import base64
import time
import hashlib
import hmac
import requests
from apps.model_provider.base_model_provider import IModelProvider, ModelProvideInfo, ModelInfo, ModelTypeConst, ModelInfoManage, BaseModelCredential, MaxKBBaseModel
from django.utils.translation import gettext as _


class XunFeiSTTModel(MaxKBBaseModel):
    """讯飞星火语音转文字模型"""
    
    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, Any], **model_kwargs):
        """创建讯飞星火语音转文字模型实例"""
        return XunFeiSTTModel(model_credential, **model_kwargs)
    
    def __init__(self, model_credential: Dict[str, Any], **model_kwargs):
        self.model_credential = model_credential
        self.model_kwargs = model_kwargs
        
    def invoke(self, audio_file: io.BytesIO):
        """调用讯飞星火语音转文字API"""
        # 获取配置信息
        app_id = self.model_credential.get('app_id')
        api_key = self.model_credential.get('api_key')
        api_secret = self.model_credential.get('api_secret')
        
        # 如果没有直接配置，尝试从credential中获取
        if not app_id or not api_key or not api_secret:
            credential = self.model_credential.get('credential', {})
            app_id = app_id or credential.get('app_id')
            api_key = api_key or credential.get('api_key')
            api_secret = api_secret or credential.get('api_secret')
            
            if not app_id or not api_key or not api_secret:
                return {'text': '语音识别失败: 缺少API配置信息'}
        
        try:
            import asyncio
            import base64
            import datetime
            import hashlib
            import hmac
            import json
            import ssl
            from urllib.parse import urlencode, urlparse
            import websockets
            
            STATUS_FIRST_FRAME = 0  # 第一帧的标识
            STATUS_CONTINUE_FRAME = 1  # 中间帧标识
            STATUS_LAST_FRAME = 2  # 最后一帧的标识
            
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # 创建认证URL
            def create_url():
                # 使用默认的WebSocket端点
                url = "wss://iat-api.xfyun.cn/v2/iat"
                host = urlparse(url).hostname
                # 生成RFC1123格式的时间戳
                gmt_format = '%a, %d %b %Y %H:%M:%S GMT'
                date = datetime.datetime.now(datetime.timezone.utc).strftime(gmt_format)

                # 拼接字符串
                signature_origin = "host: " + host + "\n"
                signature_origin += "date: " + date + "\n"
                signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
                
                # 进行hmac-sha256进行加密
                signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                                     digestmod=hashlib.sha256).digest()
                signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

                authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
                    api_key, "hmac-sha256", "host date request-line", signature_sha)
                authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
                
                # 将请求的鉴权参数组合为字典
                v = {
                    "authorization": authorization,
                    "date": date,
                    "host": host
                }
                
                # 拼接鉴权参数，生成url
                url = url + '?' + urlencode(v)
                return url
            
            # 异步处理函数
            async def recognize(input_audio_file):
                # 获取带认证的WebSocket URL
                ws_url = create_url()
                
                async with websockets.connect(ws_url, ssl=ssl_context) as ws:
                    # 处理WAV文件，提取PCM数据
                    import wave
                    import io
                    
                    # 读取所有音频数据到内存
                    input_audio_file.seek(0)
                    audio_data = input_audio_file.read()
                    
                    # 创建一个新的BytesIO对象，用于后续处理
                    audio_stream = io.BytesIO(audio_data)
                    audio_stream.seek(0)
                    
                    # 处理音频文件，提取PCM数据
                    processed_audio = None
                    
                    try:
                        # 检查是否为WAV文件
                        audio_stream.seek(0)
                        wav_header = audio_stream.read(4)
                        if wav_header == b'RIFF':
                            # 重置位置
                            audio_stream.seek(0)
                            
                            # 使用wave模块打开WAV文件
                            with wave.open(audio_stream, 'rb') as wf:
                                # 读取所有音频帧数据
                                frames = wf.readframes(wf.getnframes())
                                
                                # 创建一个新的BytesIO对象，用于存储PCM数据
                                pcm_data = io.BytesIO()
                                pcm_data.write(frames)
                                pcm_data.seek(0)
                                
                                processed_audio = pcm_data
                    except Exception as e:
                        # 处理失败，使用原始音频流
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"WAV文件处理失败: {str(e)}")
                    
                    # 如果处理成功，使用处理后的音频；否则使用原始音频数据
                    if processed_audio:
                        audio_stream = processed_audio
                    else:
                        # 重置原始音频流位置
                        audio_stream = io.BytesIO(audio_data)
                        audio_stream.seek(0)
                    
                    # 发送音频数据
                    frame_size = 8000  # 每一帧的音频大小
                    status = STATUS_FIRST_FRAME  # 音频的状态信息
                    
                    # 音频参数配置
                    business_params = {
                        "language": "zh_cn",
                        "domain": "iat",
                        "accent": "mandarin",
                        "vad_eos": 10000,
                        "aue": "raw"
                    }
                    
                    # 音频格式参数
                    audio_format = "audio/L16;rate=16000"
                    
                    while True:
                        buf = audio_stream.read(frame_size)
                        # 文件结束
                        if not buf:
                            status = STATUS_LAST_FRAME
                            # 如果是最后一帧且没有数据，直接发送结束帧
                            d = {"data": {
                                "status": 2, 
                                "format": audio_format,
                                "audio": "",
                                "encoding": "raw"
                            }}
                            await ws.send(json.dumps(d))
                            break
                        
                        # 第一帧处理
                        if status == STATUS_FIRST_FRAME:
                            d = {
                                "common": {"app_id": app_id},
                                "business": business_params,
                                "data": {
                                    "status": 0, 
                                    "format": audio_format,
                                    "audio": str(base64.b64encode(buf), 'utf-8'),
                                    "encoding": "raw"
                                }
                            }
                            await ws.send(json.dumps(d))
                            status = STATUS_CONTINUE_FRAME
                        # 中间帧处理
                        elif status == STATUS_CONTINUE_FRAME:
                            d = {"data": {
                                "status": 1, 
                                "format": audio_format,
                                "audio": str(base64.b64encode(buf), 'utf-8'),
                                "encoding": "raw"
                            }}
                            await ws.send(json.dumps(d))
                    
                    # 处理响应
                    recognized_text = ""
                    while True:
                        res = await ws.recv()
                        message = json.loads(res)
                        
                        code = message["code"]
                        if code != 0:
                            return f"语音识别失败: {code}: {message['message']}"
                        
                        data = message.get("data", {})
                        
                        # 先提取识别结果，再判断是否结束
                        result_data = data.get("result", {})
                        if result_data:
                            # 提取识别文本
                            ws_items = result_data.get("ws", [])
                            for ws_item in ws_items:
                                cw_items = ws_item.get("cw", [])
                                for cw_item in cw_items:
                                    recognized_text += cw_item.get("w", "")
                        
                        # 检查是否结束
                        if data.get("status") == 2:
                            # 识别结束
                            break
                    
                    return recognized_text
            
            # 运行异步函数，传递audio_file参数
            recognized_text = asyncio.run(recognize(audio_file))
            
            # 检查识别结果
            if not recognized_text:
                return {'text': ''}
            
            # 返回识别结果
            return {'text': recognized_text}
        except Exception as e:
            # 记录详细错误信息
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"讯飞语音转文字API调用失败: {str(e)}", exc_info=True)
            
            # 返回具体错误信息，帮助调试
            return {'text': f'语音识别失败: {str(e)}'}


class XunFeiModelProvider(IModelProvider):
    """讯飞星火模型提供商"""
    
    def __init__(self):
        # 创建模型信息管理实例
        self.model_info_manage = ModelInfoManage.builder()
        
        # 简化的凭证配置（仅包含API Key和Secret Key）
        class SimpleCredential(BaseModelCredential):
            def is_valid(self, model_type: str, model_name, model: Dict[str, object], 
                         model_params, provider, raise_exception=True):
                """验证模型认证信息"""
                return True
            
            def encryption_dict(self, model_info: Dict[str, object]):
                """加密模型认证信息"""
                return model_info
            
            def get_model_params_setting_form(self, model_name):
                """获取模型参数设置表单"""
                return [
                    {
                        "name": "api_key",
                        "label": _("API Key"),
                        "field_type": "input",
                        "required": True,
                        "placeholder": _("请输入讯飞星火API Key")
                    },
                    {
                        "name": "api_secret",
                        "label": _("API Secret"),
                        "field_type": "input",
                        "required": True,
                        "placeholder": _("请输入讯飞星火API Secret")
                    },
                    {
                        "name": "app_id",
                        "label": _("App ID"),
                        "field_type": "input",
                        "required": True,
                        "placeholder": _("请输入讯飞星火App ID")
                    },
                    {
                        "name": "base_url",
                        "label": _("Base URL"),
                        "field_type": "input",
                        "required": False,
                        "placeholder": _("请输入讯飞星火API Base URL，留空使用默认值")
                    }
                ]
        
        simple_credential = SimpleCredential()
        
        # 注册讯飞星火模型
        self.model_info_manage.append_model_info_list([
            ModelInfo('generalv3.5', '', ModelTypeConst.LLM, simple_credential, None),
            ModelInfo('generalv3', '', ModelTypeConst.LLM, simple_credential, None),
            ModelInfo('generalv2', '', ModelTypeConst.LLM, simple_credential, None),
            ModelInfo('iat', 'Chinese and English recognition', ModelTypeConst.STT, simple_credential, XunFeiSTTModel),
            ModelInfo('tts', 'Online TTS', ModelTypeConst.TTS, simple_credential, None),
            ModelInfo('tts-super-humanoid', 'Super Humanoid TTS', ModelTypeConst.TTS, simple_credential, None),
            ModelInfo('embedding', '', ModelTypeConst.EMBEDDING, simple_credential, None)
        ])
        
        # 设置默认模型
        self.model_info_manage.append_default_model_info(
            ModelInfo('generalv3.5', '', ModelTypeConst.LLM, simple_credential, None)
        )
        self.model_info_manage.append_default_model_info(
            ModelInfo('iat', 'Chinese and English recognition', ModelTypeConst.STT, simple_credential, XunFeiSTTModel)
        )
        self.model_info_manage.append_default_model_info(
            ModelInfo('tts', 'Online TTS', ModelTypeConst.TTS, simple_credential, None)
        )
        self.model_info_manage.append_default_model_info(
            ModelInfo('embedding', '', ModelTypeConst.EMBEDDING, simple_credential, None)
        )
        
        self.model_info_manage = self.model_info_manage.build()
    
    def get_model_info_manage(self):
        """获取模型信息管理器"""
        return self.model_info_manage
    
    def get_model_provide_info(self):
        """获取模型提供商信息"""
        return ModelProvideInfo(
            provider='xunfei',
            name=_('讯飞星火'),
            icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>'
        )
    
    def get_model_type_list(self):
        """获取模型类型列表"""
        return [
            {'key': _type.value.get('message'), 'value': _type.value.get('code')}
            for _type in ModelTypeConst
        ]