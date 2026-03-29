"""
测试LM Studio调用
"""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'apps.tcm.settings'
import django
django.setup()

from apps.model_provider.models import ModelConfig
from openai import OpenAI

# 获取模型配置
config = ModelConfig.objects.filter(is_delete=False, is_active=True, model_type='LLM').first()
credential = config.credential or {}
base_url = credential.get('base_url') or 'http://localhost:1234/v1'
api_key = credential.get('api_key') or 'lm-studio'
model_name = config.model_name

print(f"Model: {model_name}")
print(f"Base URL: {base_url}")

# 创建客户端
client = OpenAI(api_key=api_key, base_url=base_url, timeout=60)

# 使用IntakeAgent的系统提示词
system_prompt = """你是一名专业的中医接诊助手。你的任务是从患者描述中提取结构化信息，并以JSON格式返回。

请从患者的描述中提取以下信息：

1. **chief_complaint**（主诉）：患者最主要的不适症状，简明扼要（20字以内）。
2. **symptoms**（症状列表）：详细列出患者提到的所有症状，每个症状包含：
   - name：症状名称（如"头痛"、"失眠"、"食欲不振"）
   - duration：持续时间（如"3天"、"1周"，如患者未提及则为null）
   - severity：严重程度（轻度/中度/重度，如患者未明确则为null）
   - description：症状的详细描述（可选）
3. **age_group**（年龄段）：如患者提及年龄或年龄段（如"青年"、"中年"、"老年"），未提及则为null。
4. **gender**（性别）：如患者提及性别（"男"/"女"），未提及则为null。
5. **is_pregnant**（是否妊娠期）：如患者提及妊娠或备孕则为true，否则为false。
6. **is_minor**（是否未成年）：如患者为未成年人（18岁以下）则为true，否则为false。
7. **medical_history**（既往病史）：如患者提及既往疾病，列出疾病名称。
8. **current_medications**（当前用药）：如患者提及正在使用的药物，列出药物名称。
9. **needs_clarification**（需要澄清的问题）：如果患者描述不清晰，列出需要进一步询问的问题。

请严格只返回JSON对象，不要输出任何思考过程或解释。"""

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "患者描述：我最近总是感觉疲劳，容易出汗\n\n请严格只返回JSON对象，不要输出任何思考过程或解释。"}
]

print("\n正在调用LM Studio...")
response = client.chat.completions.create(
    model=model_name,
    messages=messages,
    temperature=0.1,
    max_tokens=1024,
)

print(f"\n响应类型: {type(response)}")
print(f"响应属性: {dir(response)}")

# 使用model_dump获取完整payload
payload = response.model_dump()
print(f"\nPayload keys: {list(payload.keys())}")

choice0 = payload.get("choices", [{}])[0]
print(f"Choice0 keys: {list(choice0.keys())}")

message0 = choice0.get("message", {})
print(f"Message0 keys: {list(message0.keys())}")

for key, value in message0.items():
    if value:
        print(f"\n{key}:")
        print(f"  长度: {len(str(value))}")
        print(f"  内容: {str(value)[:500]}...")
