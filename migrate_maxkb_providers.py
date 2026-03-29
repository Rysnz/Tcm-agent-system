#!/usr/bin/env python3
# coding=utf-8
"""
MaxKB模型提供商迁移脚本
用于将MaxKB的模型提供商迁移到当前系统
"""
import os
import shutil
import re

# MaxKB目录和当前系统目录
MAXKB_DIR = "D:\demo\MaxKB-2"
CURRENT_SYSTEM_DIR = "d:\demo\tcm-agent-system"

# 源目录和目标目录
MAXKB_PROVIDERS_DIR = os.path.join(MAXKB_DIR, "apps", "models_provider", "impl")
CURRENT_PROVIDERS_DIR = os.path.join(CURRENT_SYSTEM_DIR, "apps", "model_provider", "impl")

# 提供商列表
PROVIDERS_TO_MIGRATE = [
    "aliyun_bai_lian_model_provider",
    "anthropic_model_provider",
    "aws_bedrock_model_provider",
    "azure_model_provider",
    "deepseek_model_provider",
    "docker_ai_model_provider",
    "gemini_model_provider",
    "kimi_model_provider",
    "local_model_provider",
    "ollama_model_provider",
    "openai_model_provider",
    "regolo_model_provider",
    "siliconCloud_model_provider",
    "tencent_cloud_model_provider",
    "tencent_model_provider",
    "vllm_model_provider",
    "volcanic_engine_model_provider",
    "wenxin_model_provider",
    "xf_model_provider",
    "xinference_model_provider",
    "zhipu_model_provider"
]

def copy_provider(provider_name):
    """复制单个模型提供商"""
    source_dir = os.path.join(MAXKB_PROVIDERS_DIR, provider_name)
    target_dir = os.path.join(CURRENT_PROVIDERS_DIR, provider_name)
    
    if not os.path.exists(source_dir):
        print(f"警告：源目录不存在：{source_dir}")
        return False
    
    # 复制目录
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    
    shutil.copytree(source_dir, target_dir)
    print(f"已复制提供商：{provider_name}")
    return True

def update_provider_imports(provider_name):
    """更新提供商文件的导入语句"""
    provider_file = os.path.join(CURRENT_PROVIDERS_DIR, provider_name, f"{provider_name}.py")
    
    if not os.path.exists(provider_file):
        print(f"警告：提供商文件不存在：{provider_file}")
        return False
    
    # 读取文件内容
    with open(provider_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新导入语句
    # 将 from models_provider.xxx 替换为 from apps.model_provider.xxx
    content = re.sub(r'from models_provider\.', r'from apps.model_provider.', content)
    content = re.sub(r'from \.impl\.', r'from apps.model_provider.impl.', content)
    
    # 写回文件
    with open(provider_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"已更新提供商导入：{provider_name}")
    return True

def register_providers():
    """更新provider_manager.py文件，注册所有提供商"""
    provider_manager_file = os.path.join(CURRENT_SYSTEM_DIR, "apps", "model_provider", "provider_manager.py")
    
    if not os.path.exists(provider_manager_file):
        print(f"警告：provider_manager.py文件不存在：{provider_manager_file}")
        return False
    
    # 读取文件内容
    with open(provider_manager_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到register_builtin_providers函数
    register_func_pattern = re.compile(r'def register_builtin_providers\(\):\s*"""[\s\S]*?"""[\s\S]*?(?=\n\n# |\n\n$)')
    match = register_func_pattern.search(content)
    
    if not match:
        print("警告：未找到register_builtin_providers函数")
        return False
    
    register_func = match.group(0)
    
    # 生成导入和注册语句
    import_statements = []
    register_statements = []
    
    for provider in PROVIDERS_TO_MIGRATE:
        # 转换提供商名称为类名（首字母大写，下划线转驼峰）
        class_name = ''.join(word.capitalize() for word in provider.split('_'))
        if class_name.endswith('Provider'):
            class_name = class_name[:-8] + 'ModelProvider'
        else:
            class_name = class_name + 'ModelProvider'
        
        # 生成导入语句
        import_stmt = f"from apps.model_provider.impl.{provider}.{provider} import {class_name}"
        import_statements.append(import_stmt)
        
        # 生成注册语句
        register_stmt = f"    {provider.split('_')[0]}_provider = {class_name}()"
        register_stmt2 = f"    global_provider_manager.register_provider({provider.split('_')[0]}_provider)"
        register_statements.append(register_stmt)
        register_statements.append(register_stmt2)
    
    # 插入导入语句
    import_section = "\n".join(import_statements)
    content = re.sub(r'# 注册内置模型提供商\s*def register_builtin_providers\(\):', 
                     f'# 注册内置模型提供商\n{import_section}\n\ndef register_builtin_providers():', 
                     content)
    
    # 插入注册语句
    # 找到现有注册语句的位置
    existing_registers = re.findall(r'    # 注册[\s\S]*?global_provider_manager.register_provider\([^)]+\)', register_func)
    if existing_registers:
        # 在现有注册语句后插入新的注册语句
        last_register = existing_registers[-1]
        new_registers = "\n    \n    # 从MaxKB迁移的模型提供商\n" + "\n".join(register_statements)
        updated_register_func = register_func.replace(last_register, last_register + new_registers)
        content = content.replace(register_func, updated_register_func)
    
    # 写回文件
    with open(provider_manager_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("已更新provider_manager.py，注册所有提供商")
    return True

def main():
    """主函数"""
    print("开始迁移MaxKB模型提供商...")
    
    # 批量复制和更新提供商
    for provider in PROVIDERS_TO_MIGRATE:
        copy_provider(provider)
        update_provider_imports(provider)
    
    # 注册所有提供商
    register_providers()
    
    print("\n迁移完成！")
    print("请检查以下内容：")
    print("1. 检查所有提供商的导入语句是否正确")
    print("2. 检查provider_manager.py中的注册语句是否正确")
    print("3. 运行服务器测试是否有错误")
    print("4. 如果有错误，请根据错误信息调整代码")

if __name__ == "__main__":
    main()
