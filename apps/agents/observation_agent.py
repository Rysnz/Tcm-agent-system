"""
ObservationAgent —— 望诊融合智能体。

职责：
1. 解析用户上传的舌象/面色图片（调用视觉模型提取特征）。
2. 将视觉特征（舌色、苔色、苔厚薄、苔质、舌形、面色）结构化写入 ObservationData。
3. 若无图片，则通过对话询问舌象/面色描述。
4. 将图像特征作为下游辨证的额外证据。

多模态 MVP 策略：
- 优先使用视觉 LLM（如 GPT-4V / Qwen-VL）分析图片。
- 若视觉模型不可用，退回到文本追问模式（询问舌色等）。
- 图像分析结果只作为"辅助特征"，不单独给出诊断结论。
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from apps.agents.base_agent import BaseAgent, build_system_prompt
from apps.agents.session_state import (
    ConsultStage,
    ObservationData,
    SessionState,
)

logger = logging.getLogger("apps.agents")

_TONGUE_ANALYSIS_SYSTEM_PROMPT = build_system_prompt(
    """你是一名中医舌诊专家。请根据提供的舌象图片，提取以下特征并给出诊断结论，
以结构化 JSON 格式返回（不确定的字段填 null）：

{
  "tongue_color": "舌色：淡白/淡红/红/绛/紫（不确定填null）",
  "tongue_coating": "苔色：白/黄/灰/黑（不确定填null）",
  "coating_thickness": "苔厚薄：薄/厚（不确定填null）",
  "coating_texture": "苔质：润/燥/腻/剥落（不确定填null）",
  "tongue_shape": "舌形：正常/胖大/瘦薄/裂纹/齿痕（不确定填null）",
  "image_features": ["提取到的视觉特征描述列表"],
  "analysis_notes": "分析说明（图像质量评估、特殊发现等）",
  "diagnosis": {
    "summary": "舌象诊断总结（用通俗易懂的语言描述，2-3句话）",
    "indications": ["可能提示的身体状况列表，如：脾胃虚弱、阴虚火旺等"],
    "suggestions": ["针对舌象的调理建议列表，如：建议饮食清淡、避免辛辣等"]
  }
}

重要：
- 本分析仅供中医辅助参考，不构成诊断结论。
- 诊断结论要用通俗易懂的语言，让普通用户能理解。
- 建议要具体实用，如饮食、作息、穴位保健等。
- 如图像质量较差或特征不明显，请在 analysis_notes 中注明。
- 只输出 JSON，不要包含其他文字。"""
)

_OBSERVATION_TEXT_SYSTEM_PROMPT = build_system_prompt(
    """你是一名中医望诊助手。根据患者的文字描述，提取望诊相关信息，
并以 JSON 格式返回：

{
  "tongue_color": "舌色（淡白/淡红/红/绛/紫，不确定填null）",
  "tongue_coating": "苔色（白/黄/灰/黑，不确定填null）",
  "coating_thickness": "苔厚薄（薄/厚，不确定填null）",
  "coating_texture": "苔质（润/燥/腻/剥落，不确定填null）",
  "tongue_shape": "舌形（正常/胖大/瘦薄/裂纹/齿痕，不确定填null）",
  "face_color": "面色（红润/苍白/萎黄/晦暗/青紫，不确定填null）",
  "image_features": ["提取到的特征列表"],
  "needs_image": true/false （是否建议上传图片以便更准确分析）
}

只输出 JSON，不要包含其他文字。"""
)


class ObservationAgent(BaseAgent):
    """望诊融合 Agent（支持图像分析 + 文本回退）"""

    agent_name = "ObservationAgent"
    stage = ConsultStage.OBSERVATION

    def _execute(self, state: SessionState, **kwargs) -> SessionState:
        new_state = state.model_copy(deep=True)

        image_path: Optional[str] = kwargs.get("image_path")
        image_bytes: Optional[bytes] = kwargs.get("image_bytes")

        if image_path or image_bytes:
            # 图像分析模式
            observation = self._analyze_image(image_path, image_bytes)
        else:
            # 文本模式：从对话中提取望诊信息
            observation = self._extract_from_text(new_state)

        new_state.observation = observation
        new_state.current_stage = ConsultStage.SYNDROME
        return new_state

    def _fallback(self, state: SessionState) -> SessionState:
        """降级：跳过望诊，直接进入辨证"""
        new_state = state.model_copy(deep=True)
        new_state.current_stage = ConsultStage.SYNDROME
        new_state.add_message(
            "assistant",
            "图像分析暂时不可用，将根据症状描述进行辨证分析。"
        )
        return new_state

    # ------------------------------------------------------------------
    # 图像分析
    # ------------------------------------------------------------------

    def _analyze_image(
        self,
        image_path: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
    ) -> ObservationData:
        """调用视觉 LLM 分析舌象图片"""
        try:
            # 准备 base64 编码的图片
            if image_bytes:
                raw_bytes = image_bytes
            elif image_path:
                with open(image_path, "rb") as f:
                    raw_bytes = f.read()
            else:
                raise ValueError("No image provided")
            
            # 检查图片大小
            if len(raw_bytes) == 0:
                raise ValueError("图片文件为空")
            
            logger.info(f"原始图片大小: {len(raw_bytes)} bytes ({len(raw_bytes) / 1024 / 1024:.2f} MB)")
            
            # 检测图片格式
            mime_type = "image/jpeg"
            need_convert = False
            
            if image_path:
                suffix = Path(image_path).suffix.lower()
                logger.info(f"文件路径: {image_path}, 扩展名: {suffix}")
                
                if suffix == ".png":
                    mime_type = "image/png"
                elif suffix == ".webp":
                    mime_type = "image/webp"
                elif suffix in [".jpg", ".jpeg"]:
                    mime_type = "image/jpeg"
                elif suffix in [".heif", ".heic", ".heif-sequence"]:
                    # HEIF/HEIC 格式（苹果设备常用）需要转换为JPEG
                    mime_type = "image/heif"
                    need_convert = True
                else:
                    # 尝试从文件头检测格式
                    if raw_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                        mime_type = "image/png"
                    elif raw_bytes[:3] == b'\xff\xd8\xff':
                        mime_type = "image/jpeg"
                    elif raw_bytes[:4] == b'RIFF' and raw_bytes[8:12] == b'WEBP':
                        mime_type = "image/webp"
                    elif raw_bytes[:12].startswith(b'\x00\x00\x00') and b'ftyp' in raw_bytes[:20]:
                        # HEIF/HEIC 格式检测
                        mime_type = "image/heif"
                        need_convert = True
                        logger.info("从文件头检测到HEIF/HEIC格式")
            
            # 使用PIL进行统一的图片处理
            from PIL import Image
            import io
            
            # 注册HEIF格式支持
            if need_convert or mime_type == "image/heif":
                try:
                    from pillow_heif import register_heif_opener
                    register_heif_opener()
                    logger.info("HEIF格式支持已注册")
                except ImportError:
                    logger.warning("pillow-heif未安装，无法处理HEIF格式")
                    # 尝试直接打开，可能Pillow已经支持
            
            # 打开图片
            try:
                img = Image.open(io.BytesIO(raw_bytes))
                original_format = img.format
                original_size = img.size
                original_mode = img.mode
                logger.info(f"图片打开成功: 格式={original_format}, 尺寸={original_size}, 模式={original_mode}")
            except Exception as e:
                logger.error(f"无法打开图片: {e}")
                raise ValueError(f"无法识别图片格式，请确保上传的是有效的图片文件（支持JPG、PNG、WEBP、HEIF格式）")
            
            # 转换为RGB模式（所有格式统一处理）
            if img.mode in ['RGBA', 'LA', 'P', 'RGBX', 'RGBa']:
                # 创建白色背景
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if 'A' in img.mode or img.mode.endswith('a'):
                    rgb_img.paste(img, mask=img.split()[-1])
                else:
                    rgb_img.paste(img)
                img = rgb_img
                logger.info(f"已转换为RGB模式")
            elif img.mode != 'RGB':
                img = img.convert('RGB')
                logger.info(f"已转换为RGB模式")
            
            # 检查图片尺寸，如果太大则压缩
            # LM Studio处理图片需要大量tokens，需要更激进的压缩
            max_dimension = 768  # 降低到768像素，减少token消耗
            if max(img.size) > max_dimension:
                ratio = max_dimension / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"图片已压缩: {original_size} -> {new_size}")
            
            # 转换为JPEG格式，使用较低的质量以减小文件大小
            output_buffer = io.BytesIO()
            
            # 使用较低的JPEG质量
            quality = 70  # 固定使用较低质量，减少文件大小
            
            img.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            raw_bytes = output_buffer.getvalue()
            
            # 限制最终文件大小（最大200KB）
            max_file_size = 200 * 1024  # 200KB
            if len(raw_bytes) > max_file_size:
                # 进一步降低质量
                while len(raw_bytes) > max_file_size and quality > 30:
                    quality -= 10
                    output_buffer = io.BytesIO()
                    img.save(output_buffer, format='JPEG', quality=quality, optimize=True)
                    raw_bytes = output_buffer.getvalue()
                logger.info(f"为满足大小限制，JPEG质量调整为: {quality}")
            
            # 重新进行base64编码
            b64_image = base64.b64encode(raw_bytes).decode("ascii")
            mime_type = "image/jpeg"
            
            logger.info(f"图片处理完成: 最终大小={len(raw_bytes)} bytes ({len(raw_bytes) / 1024:.1f} KB), JPEG质量={quality}")
            
            # 验证base64编码是否正确
            try:
                decoded = base64.b64decode(b64_image)
                if len(decoded) != len(raw_bytes):
                    logger.warning("Base64编码验证失败")
            except Exception as e:
                raise ValueError(f"Base64编码错误: {e}")

            # 使用 LM Studio 本地 API 调用视觉模型
            import requests
            
            # LM Studio 本地 API 端点
            lm_studio_url = "http://localhost:1234/api/v1/chat"
            
            # 构建 data_url
            data_url = f"data:{mime_type};base64,{b64_image}"
            
            # 验证data_url格式
            if not data_url.startswith("data:image/"):
                logger.warning(f"Invalid data_url format")
            
            # 从数据库获取用户配置的视觉模型
            from apps.model_provider.models import ModelConfig
            
            # 查找 LM Studio 类型的模型配置
            lm_studio_config = ModelConfig.objects.filter(
                provider='lmstudio',
                is_active=True,
                is_delete=False
            ).first()
            
            if not lm_studio_config:
                raise RuntimeError("未找到 LM Studio 模型配置，请在模型设置中配置")
            
            # 使用用户配置的模型名称
            model_name = lm_studio_config.model_name
            logger.info(f"使用配置的模型: {model_name}")
            
            # 构建 LM Studio 格式的请求
            payload = {
                "model": model_name,
                "input": [
                    {
                        "type": "text",
                        "content": _TONGUE_ANALYSIS_SYSTEM_PROMPT + "\n\n请分析这张舌象图片，提取望诊特征。请只返回JSON，不要包含其他文字。"
                    },
                    {
                        "type": "image",
                        "data_url": data_url
                    }
                ],
                "temperature": 0.1,
                "max_output_tokens": 2048,  # 增加到2048，确保有足够空间生成JSON
                "context_length": 8192,  # 增加context长度以支持图片处理
                "stream": False
            }
            
            # 记录请求信息
            logger.info(f"调用LM Studio视觉API: {lm_studio_url}")
            logger.info(f"发送图片大小: {len(raw_bytes)} bytes ({len(raw_bytes) / 1024:.1f} KB)")
            
            response = requests.post(
                lm_studio_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            
            if response.status_code != 200:
                error_msg = response.text[:200] if response.text else "Unknown error"
                logger.error(f"LM Studio API错误: {response.status_code} - {error_msg}")
                raise RuntimeError(f"视觉模型API调用失败: {error_msg}")
            
            result = response.json()
            
            # 提取响应内容
            output = result.get("output", [])
            content = ""
            for item in output:
                if item.get("type") == "message":
                    content = item.get("content", "")
                    break
            
            if not content:
                raise RuntimeError("视觉模型未返回有效内容")
            
            logger.info(f"视觉模型响应: {content[:200]}")
            
            # 解析 JSON
            data = self._parse_json_output(content)
            return self._build_observation_from_dict(data)

        except Exception as exc:
            logger.warning(f"图片分析失败: {exc}", exc_info=True)
            # 返回降级提示
            error_hint = str(exc)[:100]
            if "HEIF" in str(exc) or "heif" in str(exc).lower():
                error_hint = "检测到HEIF格式图片，正在自动转换..."
            elif "too large" in str(exc).lower() or "过大" in str(exc):
                error_hint = "图片文件过大，请压缩到10MB以下"
            elif "format" in str(exc).lower() or "格式" in str(exc):
                error_hint = "不支持的图片格式，请使用JPG、PNG或WEBP格式"
            
            return ObservationData(
                image_features=[f"图片处理中，请稍候..."],
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"LM Studio API error: {response.status_code} - {response.text}")
            
            result = response.json()
            logger.debug(f"LM Studio response: {result}")
            
            # 提取响应内容
            output = result.get("output", [])
            content = ""
            for item in output:
                if item.get("type") == "message":
                    content = item.get("content", "")
                    break
            
            if not content:
                raise RuntimeError("No content in LM Studio response")
            
            logger.info(f"Vision model response: {content[:200]}")
            
            # 解析 JSON
            data = self._parse_json_output(content)
            return self._build_observation_from_dict(data)

        except Exception as exc:
            logger.warning("Image analysis failed: %s", exc)
            # 返回降级提示
            return ObservationData(
                image_features=[f"图像分析失败：{str(exc)[:100]}。请通过文字描述舌象情况。"],
            )

    # ------------------------------------------------------------------
    # 文本提取
    # ------------------------------------------------------------------

    def _extract_from_text(self, state: SessionState) -> ObservationData:
        """从对话文本中提取望诊信息"""
        # 收集用户消息中的望诊相关描述
        user_texts = [
            msg["content"]
            for msg in state.messages
            if msg.get("role") == "user"
        ]
        combined_text = "\n".join(user_texts[-5:])  # 只取最近 5 条

        if not combined_text.strip():
            return ObservationData()

        messages = [
            {"role": "system", "content": _OBSERVATION_TEXT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"请从以下用户描述中提取望诊信息：\n{combined_text}"
                ),
            },
        ]
        raw = self._call_llm(messages, temperature=0.1, max_tokens=512)
        data = self._parse_json_output(raw)

        # 如果建议上传图片
        if data.get("needs_image") and not state.has_image:
            state.pending_questions.append(
                "为了更准确地进行望诊分析，您可以上传舌头照片（舌象图）。"
                "如不方便，请描述您舌头的颜色和舌苔情况。"
            )

        return self._build_observation_from_dict(data)

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------

    def _build_observation_from_dict(self, data: Dict[str, Any]) -> ObservationData:
        # 处理诊断数据
        from apps.agents.session_state import TongueDiagnosis
        
        diagnosis_data = data.get("diagnosis", {})
        diagnosis = TongueDiagnosis(
            summary=diagnosis_data.get("summary", ""),
            indications=diagnosis_data.get("indications", []),
            suggestions=diagnosis_data.get("suggestions", [])
        )
        
        return ObservationData(
            tongue_color=data.get("tongue_color"),
            tongue_coating=data.get("tongue_coating"),
            coating_thickness=data.get("coating_thickness"),
            coating_texture=data.get("coating_texture"),
            tongue_shape=data.get("tongue_shape"),
            face_color=data.get("face_color"),
            image_features=data.get("image_features", []),
            image_analysis_raw=data,
            diagnosis=diagnosis,
        )
