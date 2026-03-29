# coding=utf-8
"""
    @project: TCM-Agent-System
    @file： urls.py
    @date：2026/1/11
    @desc: 用户认证相关URL配置
"""
from django.urls import path
from apps.users.views import (
    login_view,
    refresh_token_view,
    register_view,
    profile_view,
    archives_view,
    save_wellness_archive,
    save_tongue_archive,
    save_consult_archive,
    save_wellness_checkin,
    admin_stats_view,
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('refresh/', refresh_token_view, name='refresh_token'),
    path('profile/', profile_view, name='profile'),
    path('archives/', archives_view, name='archives'),
    path('archives/wellness/', save_wellness_archive, name='save_wellness_archive'),
    path('archives/wellness/checkin/', save_wellness_checkin, name='save_wellness_checkin'),
    path('archives/tongue/', save_tongue_archive, name='save_tongue_archive'),
    path('archives/consult/', save_consult_archive, name='save_consult_archive'),
    path('admin/stats/', admin_stats_view, name='admin_stats'),
]
