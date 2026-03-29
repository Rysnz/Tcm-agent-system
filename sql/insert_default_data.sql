-- 插入默认中医问诊应用
INSERT INTO tcm_application (id, name, desc, user_id, work_flow, model_config, knowledge_bases, tools, prompt_template, is_active, is_delete, create_time, update_time)
VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  '中医智能问诊',
  '默认的中医智能问诊应用，支持辨证、方剂推荐、古籍检索等功能',
  '00000000-0000-0000-000000000001',
  '{
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
  }',
  '{}',
  '[]',
  '[]',
  '你是一个专业的中医医生助手。请根据用户的症状进行辨证分析，并推荐合适的方剂。\n\n注意事项：\n1. 详细询问症状\n2. 进行辨证分析\n3. 推荐经典方剂\n4. 说明用法用量\n5. 提醒注意事项和禁忌',
  true,
  false,
  CURRENT_TIMESTAMP,
  CURRENT_TIMESTAMP
);

-- 插入默认知识库
INSERT INTO tcm_knowledge_base (id, name, desc, user_id, meta, is_active, is_delete, create_time, update_time)
VALUES (
  '550e8400-e29b-41d4-a716-4466554400001',
  '中医知识库',
  '包含中医经典古籍、方剂、药材等专业内容',
  '00000000-0000-0000-000000000001',
  '{"type": "tcm", "description": "中医专业知识库"}',
  true,
  false,
  CURRENT_TIMESTAMP,
  CURRENT_TIMESTAMP
);

-- 插入默认工具
INSERT INTO tcm_tool (id, name, desc, tool_type, tool_config, is_active, is_system, is_delete, create_time, update_time)
VALUES 
  ('550e8400-e29b-41d4-a716-4466554400002', '辨证分析', '根据症状进行中医辨证分析', 'diagnosis', '{}', true, true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('550e8400-e29b-41d4-a716-4466554400003', '方剂推荐', '根据证型推荐经典方剂', 'prescription_search', '{}', true, true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('550e8400-e29b-41d4-a716-4466554400004', '药材查询', '查询药材功效、禁忌、用量', 'herb_query', '{}', true, true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('550e8400-e29b-41d4-a716-4466554400005', '古籍检索', '检索中医经典古籍文献', 'classic_search', '{}', true, true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('550e8400-e29b-41d4-a716-4466554400006', '配伍禁忌检查', '检查方剂中的配伍禁忌（十八反、十九畏）', 'contraindication_check', '{}', true, true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
