import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.tcm.settings')
django.setup()

from apps.application.models import Application
from apps.knowledge.models import KnowledgeBase
from apps.tools.models import Tool
import json

def create_default_application():
    if Application.objects.filter(name='中医智能问诊').exists():
        print('应用"中医智能问诊"已存在，跳过创建')
        return
    
    workflow_config = {
        "nodes": [
            {
                "id": "start",
                "type": "start",
                "data": {
                    "label": "开始",
                    "description": "中医问诊开始"
                },
                "position": {"x": 50, "y": 100}
            },
            {
                "id": "symptom_collection",
                "type": "llm",
                "data": {
                    "label": "症状采集",
                    "description": "收集用户症状信息",
                    "model_config": {
                        "model": "mimo-v2-flash",
                        "temperature": 0.7
                    },
                    "prompt_template": "你是一个专业的中医问诊助手。请根据用户的描述，提取关键症状信息。\n\n用户描述：{user_query}\n\n请提取以下信息：\n1. 主要症状\n2. 伴随症状\n3. 舌苔情况\n4. 脉象情况\n\n以JSON格式返回。"
                },
                "position": {"x": 300, "y": 100}
            },
            {
                "id": "diagnosis",
                "type": "tool_call",
                "data": {
                    "label": "辨证分析",
                    "description": "根据症状进行中医辨证",
                    "tool_name": "diagnosis",
                    "param_mapping": {
                        "symptoms": "extracted_symptoms"
                    }
                },
                "position": {"x": 500, "y": 100}
            },
            {
                "id": "knowledge_retrieval",
                "type": "knowledge_retrieval",
                "data": {
                    "label": "知识库检索",
                    "description": "从中医知识库检索相关信息",
                    "knowledge_base_id": "{knowledge_base_id}",
                    "top_k": 4
                },
                "position": {"x": 700, "y": 100}
            },
            {
                "id": "prescription",
                "type": "tool_call",
                "data": {
                    "label": "方剂推荐",
                    "description": "根据证型推荐方剂",
                    "tool_name": "prescription_search",
                    "param_mapping": {
                        "syndrome": "diagnosis_result.syndrome"
                    }
                },
                "position": {"x": 900, "y": 100}
            },
            {
                "id": "end",
                "type": "end",
                "data": {
                    "label": "结束",
                    "description": "问诊结束"
                },
                "position": {"x": 1100, "y": 100}
            }
        ],
        "edges": [
            {
                "id": "e1",
                "source": "start",
                "target": "symptom_collection",
                "data": {}
            },
            {
                "id": "e2",
                "source": "symptom_collection",
                "target": "diagnosis",
                "data": {}
            },
            {
                "id": "e3",
                "source": "diagnosis",
                "target": "knowledge_retrieval",
                "data": {}
            },
            {
                "id": "e4",
                "source": "knowledge_retrieval",
                "target": "prescription",
                "data": {}
            },
            {
                "id": "e5",
                "source": "prescription",
                "target": "end",
                "data": {}
            }
        ]
    }
    
    app = Application.objects.create(
        name='中医智能问诊',
        desc='默认的中医智能问诊应用，支持辨证、方剂推荐、古籍检索等功能',
        user_id=uuid.uuid4(),
        work_flow=json.dumps(workflow_config),
        model_config=json.dumps({}),
        knowledge_bases=json.dumps([]),
        tools=json.dumps([]),
        prompt_template='你是一个专业的中医医生助手。请根据用户的症状进行辨证分析，并推荐合适的方剂。\n\n注意事项：\n1. 详细询问症状\n2. 进行辨证分析\n3. 推荐经典方剂\n4. 说明用法用量\n5. 提醒注意事项和禁忌',
        is_active=True,
        is_delete=False
    )
    print(f'✓ 创建应用: {app.name}')

def create_default_knowledge_base():
    if KnowledgeBase.objects.filter(name='中医知识库').exists():
        print('知识库"中医知识库"已存在，跳过创建')
        return
    
    kb = KnowledgeBase.objects.create(
        name='中医知识库',
        desc='包含中医经典古籍、方剂、药材等专业内容',
        user_id=uuid.uuid4(),
        meta=json.dumps({"type": "tcm", "description": "中医专业知识库"}),
        is_active=True,
        is_delete=False
    )
    print(f'✓ 创建知识库: {kb.name}')

def create_default_tools():
    tools_data = [
        {
            'name': '辨证分析',
            'desc': '根据症状进行中医辨证分析',
            'tool_type': 'diagnosis',
            'tool_config': json.dumps({})
        },
        {
            'name': '方剂推荐',
            'desc': '根据证型推荐经典方剂',
            'tool_type': 'prescription_search',
            'tool_config': json.dumps({})
        },
        {
            'name': '药材查询',
            'desc': '查询药材功效、禁忌、用量',
            'tool_type': 'herb_query',
            'tool_config': json.dumps({})
        },
        {
            'name': '古籍检索',
            'desc': '检索中医经典古籍文献',
            'tool_type': 'classic_search',
            'tool_config': json.dumps({})
        },
        {
            'name': '配伍禁忌检查',
            'desc': '检查方剂中的配伍禁忌（十八反、十九畏）',
            'tool_type': 'contraindication_check',
            'tool_config': json.dumps({})
        }
    ]
    
    for tool_data in tools_data:
        if Tool.objects.filter(name=tool_data['name']).exists():
            print(f'工具"{tool_data["name"]}"已存在，跳过创建')
            continue
        
        tool = Tool.objects.create(
            name=tool_data['name'],
            desc=tool_data['desc'],
            tool_type=tool_data['tool_type'],
            tool_config=tool_data['tool_config'],
            is_active=True,
            is_system=True,
            is_delete=False
        )
        print(f'✓ 创建工具: {tool.name}')

def main():
    print('========================================')
    print('开始插入默认数据...')
    print('========================================\n')
    
    try:
        create_default_application()
        print()
        create_default_knowledge_base()
        print()
        create_default_tools()
        print()
        print('========================================')
        print('默认数据插入完成！')
        print('========================================')
        print('\n已创建：')
        print('  - 1个应用：中医智能问诊')
        print('  - 1个知识库：中医知识库')
        print('  - 5个工具：辨证分析、方剂推荐、药材查询、古籍检索、配伍禁忌检查')
    except Exception as e:
        print(f'\n错误: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
