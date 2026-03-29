from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from apps.users.models import UserProfile, WellnessArchive, TongueAnalysisArchive, ConsultArchive

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


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, min_length=3, max_length=20)
    password = serializers.CharField(required=True, min_length=6, max_length=32, write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    display_name = serializers.CharField(required=False, allow_blank=True, max_length=64)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('用户名已存在')
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'display_name', 'phone', 'avatar', 'create_time', 'update_time']


class WellnessArchiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = WellnessArchive
        fields = ['id', 'constitution', 'cycle_days', 'source_syndrome', 'plan_json', 'create_time', 'update_time']


class TongueAnalysisArchiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = TongueAnalysisArchive
        fields = ['id', 'session_id', 'image_name', 'analysis_json', 'create_time']


class ConsultArchiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultArchive
        fields = [
            'id',
            'session_id',
            'title',
            'current_stage',
            'latest_question',
            'latest_answer',
            'is_high_risk',
            'create_time',
            'update_time',
        ]
