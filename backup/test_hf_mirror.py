import os
import sys

# 设置Django环境变量
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.tcm.settings')

# 初始化Django
import django
django.setup()

# 测试HF_ENDPOINT设置
print(f"当前HF_ENDPOINT: {os.environ.get('HF_ENDPOINT')}")
print(f"PYTHONHTTPSVERIFY: {os.environ.get('PYTHONHTTPSVERIFY')}")

# 测试SentenceTransformer模型加载
from sentence_transformers import SentenceTransformer

try:
    print("正在测试加载BAAI/bge-large-zh-v1.5模型...")
    model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
    print("模型加载成功！")
    
    # 测试模型编码功能
    test_text = "这是一个测试文本"
    embedding = model.encode(test_text, convert_to_numpy=True)
    print(f"模型编码成功，向量维度: {len(embedding)}")
    
except Exception as e:
    print(f"模型加载失败: {type(e).__name__}, 错误信息: {str(e)}")
    import traceback
    traceback.print_exc()
