"""
下载bge-m3模型到本地目录
"""
import os
import sys

# 设置Hugging Face镜像源
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

# 设置模型下载路径
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models', 'embedding', 'bge-m3')
os.makedirs(MODEL_DIR, exist_ok=True)

print(f"下载目录: {MODEL_DIR}")
print(f"HF_ENDPOINT: {os.environ.get('HF_ENDPOINT')}")

try:
    from huggingface_hub import snapshot_download
    
    print("\n开始下载BAAI/bge-m3模型...")
    print("这可能需要几分钟，请耐心等待...")
    
    # 使用snapshot_download下载整个模型仓库
    # 添加allow_patterns排除不必要的文件
    path = snapshot_download(
        repo_id="BAAI/bge-m3",
        local_dir=MODEL_DIR,
        local_dir_use_symlinks=False,  # 不使用符号链接，直接复制文件
        resume_download=True,  # 支持断点续传
        allow_patterns=[
            "*.json",
            "*.txt", 
            "*.bin",
            "*.safetensors",
            "*.py",
            "*.md",
            "*.yaml",
            "*.yml",
            "*.cfg",
        ],  # 只下载模型相关文件
    )
    
    print(f"\n下载完成！模型路径: {path}")
    
    # 列出下载的文件
    print("\n下载的文件列表:")
    for item in os.listdir(MODEL_DIR):
        item_path = os.path.join(MODEL_DIR, item)
        if os.path.isfile(item_path):
            size = os.path.getsize(item_path)
            print(f"  - {item} ({size / 1024 / 1024:.2f} MB)")
        else:
            print(f"  - {item}/")
            
except Exception as e:
    print(f"\n下载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

