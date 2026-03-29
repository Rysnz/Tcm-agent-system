"""
测试SyndromeAgent的_fallback方法
"""
import os
import sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'apps.tcm.settings'
import django
django.setup()

# 设置标准输出编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from apps.agents.syndrome_agent import SyndromeAgent
from apps.agents.session_state import SessionState, SymptomInfo

# 创建状态
state = SessionState()
state.chief_complaint = '头疼、手脚冰凉'
state.symptoms = [
    SymptomInfo(name='头疼'),
    SymptomInfo(name='手脚冰凉'),
]
state.inquiry_answers = {
    '寒热': '怕热',
    '汗液': '盗汗',
    '头身': '头疼',
    '大便': '大便干燥',
}
state.messages = [
    {'role': 'user', 'content': '头疼、手脚冰冷好几年了'},
    {'role': 'user', 'content': '好几年了，白天晚上都差不多'},
    {'role': 'user', 'content': '怕热，体温36.9.晚上睡觉会盗汗'},
    {'role': 'user', 'content': '头疼，大便干燥'},
]

# 创建agent
agent = SyndromeAgent()

# 执行_fallback方法
result = agent._fallback(state)

print(f'Primary syndrome: {result.primary_syndrome}')
print(f'Syndrome candidates: {[(c.name, c.confidence) for c in result.syndrome_candidates]}')
print(f'Assistant message: {result.messages[-1] if result.messages else "None"}')
