from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import User
import logging
import os

logger = logging.getLogger('apps.users')

@receiver(post_migrate)
def create_admin_user(sender, **kwargs):
    """系统启动时创建admin用户"""
    try:
        # 检查是否已存在admin用户
        User.objects.get(username='admin')
    except User.DoesNotExist:
        # 创建admin用户，密码为admin
        admin_password = (
            os.environ.get('DEFAULT_ADMIN_PASSWORD')
            or os.environ.get('DJANGO_SUPERUSER_PASSWORD')
            or 'admin'
        )
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password=admin_password
        )
        if admin_password == 'admin':
            logger.warning('Created default admin user with development password; set DEFAULT_ADMIN_PASSWORD in production.')
        else:
            logger.info('Created default admin user from environment configuration.')
