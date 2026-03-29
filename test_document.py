"""
测试文档处理
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.tcm.settings')
sys.path.insert(0, '.')
django.setup()

from apps.knowledge.models import KnowledgeBase, Document
from apps.knowledge.task.document_processor import DocumentProcessor

# 获取知识库
kb = KnowledgeBase.objects.filter(is_delete=False).first()
print(f"知识库: {kb.name} ({kb.id})")

# 获取失败的文档
doc = Document.objects.filter(status='failed').first()
if not doc:
    print("没有失败的文档")
    sys.exit(1)

print(f"\n文档信息:")
print(f"  ID: {doc.id}")
print(f"  名称: {doc.name}")
print(f"  文件类型: {doc.file_type}")
print(f"  文件路径: {doc.file_path}")
print(f"  状态: {doc.status}")

# 检查文件是否存在
if os.path.exists(doc.file_path):
    print(f"  文件大小: {os.path.getsize(doc.file_path)} bytes")
else:
    print(f"  [ERROR] 文件不存在!")
    sys.exit(1)

# 尝试创建处理器并处理文档
print("\n开始处理文档...")
try:
    processor = DocumentProcessor(str(kb.id))
    print("处理器创建成功")
    
    # 提取文本
    print("提取文本...")
    paragraphs = processor._extract_text(doc.file_path, doc.file_type)
    print(f"提取了 {len(paragraphs)} 个段落")
    
    # 显示前3个段落
    for i, para in enumerate(paragraphs[:3]):
        print(f"  段落{i+1}: {para['content'][:100]}...")
    
    # 处理段落
    print("\n处理段落和生成向量...")
    processor._process_paragraphs(doc, paragraphs)
    
    # 更新文档状态
    doc.status = 'completed'
    doc.char_count = sum(len(p['content']) for p in paragraphs)
    doc.paragraph_count = len(paragraphs)
    doc.progress = 100
    doc.save()
    
    print(f"\n处理完成!")
    print(f"  字符数: {doc.char_count}")
    print(f"  段落数: {doc.paragraph_count}")
    
except Exception as e:
    print(f"\n处理失败: {e}")
    import traceback
    traceback.print_exc()
