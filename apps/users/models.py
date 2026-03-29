from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """用户扩展信息"""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=64, blank=True, default='')
    phone = models.CharField(max_length=32, blank=True, default='')
    avatar = models.TextField(blank=True, default='')
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profile'
        verbose_name = '用户档案'
        verbose_name_plural = verbose_name


class WellnessArchive(models.Model):
    """养生档案（登录用户持久化）"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wellness_archives')
    constitution = models.CharField(max_length=64)
    cycle_days = models.IntegerField(default=7)
    source_syndrome = models.CharField(max_length=128, blank=True, default='')
    plan_json = models.JSONField(default=dict)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wellness_archive'
        verbose_name = '养生档案'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']


class TongueAnalysisArchive(models.Model):
    """舌象分析档案（登录用户持久化）"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tongue_archives')
    session_id = models.CharField(max_length=128, blank=True, default='')
    image_name = models.CharField(max_length=256, blank=True, default='')
    analysis_json = models.JSONField(default=dict)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tongue_analysis_archive'
        verbose_name = '舌象分析档案'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']


class ConsultArchive(models.Model):
    """智能问诊档案（登录用户持久化）"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='consult_archives')
    session_id = models.CharField(max_length=128, db_index=True)
    title = models.CharField(max_length=128, default='问诊会话')
    current_stage = models.CharField(max_length=32, default='inquiry')
    latest_question = models.TextField(blank=True, default='')
    latest_answer = models.TextField(blank=True, default='')
    is_high_risk = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'consult_archive'
        verbose_name = '问诊档案'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']
        constraints = [
            models.UniqueConstraint(fields=['user', 'session_id'], name='uniq_consult_archive_user_session'),
        ]
