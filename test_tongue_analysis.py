# -*- coding: utf-8 -*-
"""
舌象分析测试脚本
"""
import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.tcm.settings')

import django
django.setup()

from apps.agents.base_agent import BaseAgent

# 测试 JSON 解析
test_cases = [
    # 测试用例 1: 直接 JSON
    '{"tongue_color": "淡红", "tongue_coating": "白", "coating_thickness": "薄", "coating_texture": "润", "tongue_shape": "正常"}',
    
    # 测试用例 2: 带代码块标记的 JSON
    '```json\n{"tongue_color": "淡红", "tongue_coating": "白"}\n```',
    
    # 测试用例 3: 带前导换行的 JSON
    '\n\n{\n  "tongue_color": "淡红",\n  "tongue_coating": "白"\n}',
]

for i, test_case in enumerate(test_cases, 1):
    print(f"\n=== 测试用例 {i} ===")
    print(f"输入: {test_case[:50]}...")
    result = BaseAgent._parse_json_output(test_case)
    print(f"解析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
