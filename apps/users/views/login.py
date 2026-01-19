# coding=utf-8
"""
    @project: TCM-Agent-System
    @file： login.py
    @date：2026/1/11
    @desc: 登录视图
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from djangorestframework_simplejwt.tokens import RefreshToken


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """登录视图"""
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'detail': '用户名和密码不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 使用Django内置的认证系统验证用户名和密码
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response(
                {'detail': '用户名或密码错误'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # 检查用户是否激活
        if not user.is_active:
            return Response(
                {'detail': '用户已被禁用，请联系管理员'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # 生成JWT令牌
        refresh = RefreshToken.for_user(user)
        
        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_staff': user.is_staff
                }
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'detail': str(e)},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """刷新令牌视图"""
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response(
            {'detail': '刷新令牌不能为空'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        
        return Response(
            {
                'access': access_token,
                'refresh': refresh_token
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'detail': '无效的刷新令牌'},
            status=status.HTTP_401_UNAUTHORIZED
        )
