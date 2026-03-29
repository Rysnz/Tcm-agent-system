"""
测试LLM调用
"""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'apps.tcm.settings'
import django
django.setup()

from apps.model_provider.models import ModelConfig
from apps.model_provider.provider_manager import global_provider_manager
from apps.agents.base_agent import _normalize_lmstudio_base_url
from openai import OpenAI
import json

# 查询激活的LLM模型
config = ModelConfig.objects.filter(
    is_delete=False, 
    is_active=True, 
    model_type='LLM'
).first()

if not config:
    print("No active LLM model found")
    exit(1)

print(f"Model: {config.name}")
print(f"Provider: {config.provider}")
print(f"Model name: {config.model_name}")
print(f"Credential: {config.credential}")

# 测试LM Studio调用
if config.provider == "lmstudio":
    credential = config.credential or {}
    base_url = _normalize_lmstudio_base_url(str(credential.get("base_url") or "http://localhost:1234/v1"))
    api_key = credential.get("api_key") or "lm-studio"
    model_name = str(credential.get("model") or config.model_name)
    
    print(f"\nBase URL: {base_url}")
    print(f"Model name: {model_name}")
    
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=30)
    
    messages = [
        {"role": "system", "content": "你是一个中医助手。请用JSON格式返回响应。"},
        {"role": "user", "content": "请返回一个简单的JSON对象"}
    ]
    
    print("\nCalling LM Studio...")
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.1,
            max_tokens=256,
        )
        
        payload = completion.model_dump()
        choice0 = (payload.get("choices") or [{}])[0]
        message0 = choice0.get("message") or {}
        
        print(f"\nResponse:")
        print(f"  Content: {message0.get('content', '')[:200]}")
        print(f"  Reasoning: {message0.get('reasoning_content', '')[:200]}")
        
        # 测试JSON提取
        text = message0.get("content") or ""
        if text:
            # 提取JSON
            import re
            for m in re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE):
                snippet = m.group(1).strip()
                try:
                    obj = json.loads(snippet)
                    print(f"\nExtracted JSON: {obj}")
                except Exception as e:
                    print(f"\nJSON parse error: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
