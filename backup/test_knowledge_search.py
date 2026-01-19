import os
import sys

# 设置Django环境变量
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.tcm.settings')

# 初始化Django
import django
django.setup()

# 导入所需模型和类
from apps.knowledge.vector.pg_vector import PGVectorStore
from apps.knowledge.models import KnowledgeBase

try:
    # 获取第一个知识库
    knowledge_base = KnowledgeBase.objects.first()
    if not knowledge_base:
        print("没有找到知识库，请先创建一个知识库并上传文档")
        sys.exit(1)
    
    print(f"使用知识库: {knowledge_base.name} (ID: {knowledge_base.id})")
    
    # 初始化向量存储
    config = {
        'knowledge_base_id': str(knowledge_base.id),
        'embedding_model': 'BAAI/bge-large-zh-v1.5',
        'dimension': 1024
    }
    
    vector_store = PGVectorStore(config)
    
    # 测试查询
    test_query = "竞赛活动奖励"
    print(f"\n测试查询: {test_query}")
    
    results = vector_store.similarity_search(test_query, k=3)
    print(f"检索结果: {len(results)} 条")
    
    for i, result in enumerate(results):
        print(f"\n结果 {i+1}:")
        print(f"标题: {result.get('title', '')}")
        print(f"内容: {result.get('content', '')[:100]}...")
        print(f"页码: {result.get('page_number', '')}")
        print(f"元数据: {result.get('meta', {})}")
    
    # 测试similarity_search_with_score
    print(f"\n测试带分数的检索:")
    results_with_score = vector_store.similarity_search_with_score(test_query, k=3)
    for i, result in enumerate(results_with_score):
        print(f"\n结果 {i+1} (相似度: {result['score']:.4f}):")
        print(f"标题: {result.get('title', '')}")
        print(f"内容: {result.get('content', '')[:100]}...")
        
    print("\n检索测试成功！")
    
except Exception as e:
    print(f"检索测试失败: {type(e).__name__}, 错误信息: {str(e)}")
    import traceback
    traceback.print_exc()
