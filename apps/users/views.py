from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """登录视图"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    # 简单的认证逻辑
    user = authenticate(username=username, password=password)
    
    if user:
        # 生成JWT token
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff,
                'is_active': user.is_active
            }
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'detail': '用户名或密码错误'
        }, status=status.HTTP_401_UNAUTHORIZED)

class UserCreateView(generics.CreateAPIView):
    """创建用户视图"""
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        # 设置密码
        serializer.save(password=self.request.data.get('password'))
