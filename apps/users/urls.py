# coding=utf-8
"""
    @project: TCM-Agent-System
    @file： urls.py
    @date：2026/1/11
    @desc: 用户认证相关URL配置
"""
from django.urls import path
from apps.users.views.login import login_view, refresh_token_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('refresh/', refresh_token_view, name='refresh_token'),
]
