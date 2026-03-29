# 调试模型提供商注册
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 直接测试讯飞模型提供商的注册
    from apps.model_provider.impl.xunfei_model_provider import XunFeiModelProvider
    print("✓ 成功导入XunFeiModelProvider")
    
    # 初始化Django设置（如果需要）
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            USE_I18N=False,
            INSTALLED_APPS=[
                'apps.model_provider',
            ],
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
        )
        django.setup()
    
    # 创建并注册提供商
    from apps.model_provider.provider_manager import global_provider_manager
    
    # 清除现有提供商
    global_provider_manager.provider_dict.clear()
    global_provider_manager.provider_list.clear()
    
    # 手动注册讯飞模型提供商
    xunfei_provider = XunFeiModelProvider()
    global_provider_manager.register_provider(xunfei_provider)
    print("✓ 成功注册XunFeiModelProvider")
    
    # 测试获取提供商
    provider = global_provider_manager.get_provider('xunfei')
    if provider:
        print("✓ 成功获取xunfei提供商")
        provider_info = provider.get_model_provide_info()
        print(f"提供商信息: {provider_info}")
    else:
        print("✗ 无法获取xunfei提供商")
        print(f"当前注册的提供商: {list(global_provider_manager.provider_dict.keys())}")
        
    # 测试注册所有提供商
    print("\n正在测试注册所有内置提供商...")
    from apps.model_provider.provider_manager import register_builtin_providers
    register_builtin_providers()
    print(f"✓ 完成注册所有提供商")
    print(f"注册的提供商数量: {len(global_provider_manager.provider_list)}")
    print(f"注册的提供商: {list(global_provider_manager.provider_dict.keys())}")
    
except Exception as e:
    print(f"✗ 错误: {str(e)}")
    import traceback
    traceback.print_exc()
