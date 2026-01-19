from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'is_active']
        read_only_fields = ['id', 'is_staff', 'is_active']

class LoginSerializer(serializers.Serializer):
    """登录序列化器"""
    username = serializers.CharField(required=True, label='用户名')
    password = serializers.CharField(required=True, label='密码', write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(request=self.context.get('request'),
                              username=username, password=password)
            
            if not user:
                raise serializers.ValidationError('用户名或密码错误', code='authorization')
        else:
            raise serializers.ValidationError('必须提供用户名和密码', code='authorization')
        
        attrs['user'] = user
        return attrs
