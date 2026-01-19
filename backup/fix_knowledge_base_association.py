import os
import sys
import django

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.tcm.settings')

# 初始化Django
django.setup()

from apps.application.models import Application
from apps.knowledge.models import KnowledgeBase

print("=== 修复知识库关联 ===")

# 获取所有应用
applications = Application.objects.all()

# 获取所有知识库
knowledge_bases = KnowledgeBase.objects.filter(is_delete=False, is_active=True)
knowledge_base_ids = [str(kb.id) for kb in knowledge_bases]

print(f"找到 {len(knowledge_bases)} 个激活的知识库")
for kb in knowledge_bases:
    print(f"  知识库: {kb.name} (ID: {kb.id})")

# 为每个应用关联所有知识库
for app in applications:
    print(f"\n处理应用: {app.name} (ID: {app.id})")
    print(f"  当前关联的知识库: {app.knowledge_bases}")
    
    # 处理现有的知识库，确保是列表格式
    current_kb = app.knowledge_bases
    if isinstance(current_kb, str):
        # 如果是字符串，尝试解析为JSON列表
        import json
        try:
            current_kb = json.loads(current_kb)
            print(f"  已将字符串解析为列表: {current_kb}")
        except json.JSONDecodeError:
            # 如果解析失败，使用空列表
            current_kb = []
            print(f"  字符串格式无效，使用空列表")
    elif not isinstance(current_kb, list):
        # 如果不是列表，使用空列表
        current_kb = []
        print(f"  类型无效，使用空列表")
    
    # 合并现有的知识库和所有激活的知识库
    updated_knowledge_bases = list(set(current_kb + knowledge_base_ids))
    
    if updated_knowledge_bases != current_kb:
        app.knowledge_bases = updated_knowledge_bases
        app.save()
        print(f"  已更新知识库关联: {updated_knowledge_bases}")
    else:
        print(f"  知识库关联已正确设置，无需更新")

print("\n=== 修复完成 ===")
