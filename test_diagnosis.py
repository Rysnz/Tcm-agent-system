"""
诊断LLM调用问题的测试脚本
"""
import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'apps.tcm.settings'

import django
django.setup()

from apps.model_provider.models import ModelConfig
from apps.model_provider.provider_manager import global_provider_manager
from apps.agents.intake_agent import IntakeAgent
from apps.agents.session_state import SessionState

print("=" * 60)
print("TCM Agent 诊断测试")
print("=" * 60)

# 1. 检查模型配置
print("\n[1] 检查LLM模型配置...")
configs = ModelConfig.objects.filter(is_delete=False, model_type='LLM')
print(f"找到 {configs.count()} 个LLM模型配置")
for config in configs:
    print(f"  - {config.name}")
    print(f"    Provider: {config.provider}")
    print(f"    Model: {config.model_name}")
    print(f"    Active: {config.is_active}")
    # 获取base_url从credential或params
    credential = config.credential or {}
    params = config.params or {}
    base_url = credential.get('base_url') or params.get('base_url') or 'N/A'
    print(f"    Base URL: {base_url}")
    if credential:
        api_key = credential.get('api_key', '')
        if api_key:
            print(f"    API Key: {api_key[:10]}...")
        else:
            print(f"    API Key: (empty)")

# 2. 获取激活的模型
print("\n[2] 获取激活的LLM模型...")
active_config = ModelConfig.objects.filter(
    is_delete=False, 
    is_active=True, 
    model_type='LLM'
).first()

if not active_config:
    print("[ERROR] 没有找到激活的LLM模型！")
    sys.exit(1)

print(f"[OK] 激活模型: {active_config.name}")

# 3. 测试Provider调用
print("\n[3] 测试Provider调用...")
try:
    provider = global_provider_manager.get_provider(active_config.provider)
    if not provider:
        print(f"[ERROR] Provider '{active_config.provider}' 未找到")
        sys.exit(1)
    print(f"[OK] Provider获取成功: {type(provider).__name__}")
except Exception as e:
    print(f"[ERROR] Provider获取失败: {e}")
    sys.exit(1)

# 3.1 直接测试LM Studio调用
print("\n[3.1] 直接测试LM Studio调用...")
try:
    from openai import OpenAI
    
    credential = active_config.credential or {}
    base_url = credential.get('base_url') or 'http://localhost:1234/v1'
    api_key = credential.get('api_key') or 'lm-studio'
    model_name = active_config.model_name
    
    print(f"Base URL: {base_url}")
    print(f"Model: {model_name}")
    
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=30)
    
    # 使用与IntakeAgent相同的系统提示词
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
        {"role": "user", "content": f"患者描述：我最近总是感觉疲劳，容易出汗\n\n请严格只返回JSON对象，不要输出任何思考过程或解释。"}
    ]
    
    print("正在调用LM Studio...")
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.1,
        max_tokens=1024,
    )
    
    content = response.choices[0].message.content
    print(f"[OK] LM Studio响应成功")
    print(f"\n完整响应内容:\n{content}")
    
    # 尝试解析JSON
    import json
    import re
    
    # 提取JSON对象
    def extract_json(text):
        if not text:
            return None
        
        # 1. 尝试整体解析
        try:
            obj = json.loads(text.strip())
            if isinstance(obj, dict):
                return obj
        except:
            pass
        
        # 2. 查找```json代码块
        for m in re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE):
            snippet = m.group(1).strip()
            try:
                obj = json.loads(snippet)
                if isinstance(obj, dict):
                    return obj
            except:
                continue
        
        # 3. 平衡大括号扫描
        stack = []
        candidates = []
        for idx, ch in enumerate(text):
            if ch == "{":
                stack.append(idx)
            elif ch == "}" and stack:
                start = stack.pop()
                if not stack:
                    candidates.append(text[start:idx + 1])
        
        for candidate in reversed(candidates):
            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict):
                    return obj
            except:
                continue
        
        return None
    
    parsed = extract_json(content)
    if parsed:
        print(f"\n[OK] JSON解析成功")
        print(f"JSON keys: {list(parsed.keys())}")
    else:
        print(f"\n[ERROR] 无法解析JSON")
    
except Exception as e:
    print(f"[ERROR] LM Studio调用失败: {e}")
    import traceback
    traceback.print_exc()

# 4. 测试IntakeAgent
print("\n[4] 测试IntakeAgent...")
try:
    agent = IntakeAgent()
    state = SessionState()
    state.add_message('user', '我最近总是感觉疲劳，容易出汗')
    
    print("正在调用IntakeAgent...")
    result = agent.run(state)
    
    print(f"[OK] IntakeAgent执行成功")
    print(f"  Chief complaint: {result.chief_complaint}")
    print(f"  Symptoms: {[s.name for s in result.symptoms]}")
    print(f"  Stage: {result.current_stage}")
    print(f"  Agent records: {len(result.agent_call_records)}")
    
    for rec in result.agent_call_records:
        status = "[OK]" if rec.success else "[FAIL]"
        error_msg = rec.error_msg if rec.error_msg else 'success'
        print(f"    {status} {rec.agent_name}: {error_msg}")
        
except Exception as e:
    print(f"[ERROR] IntakeAgent执行失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
