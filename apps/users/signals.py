from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_migrate)
def create_admin_user(sender, **kwargs):
    """系统启动时创建admin用户"""
    try:
        # 检查是否已存在admin用户
        User.objects.get(username='admin')
    except User.DoesNotExist:
        # 创建admin用户，密码为admin
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin'
        )
        print('Created admin user: username=admin, password=admin')
