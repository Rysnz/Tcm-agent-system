from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import UserProfile, WellnessArchive, TongueAnalysisArchive
from apps.users.serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    WellnessArchiveSerializer,
    TongueAnalysisArchiveSerializer,
    ConsultArchiveSerializer,
)
from apps.users.models import ConsultArchive


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    payload = dict(request.data or {})
    username = payload.get('username', '')
    password = payload.get('password', '')
    email = payload.get('email', '')
    display_name = payload.get('display_name', '')

    user = User.objects.create_user(username=username, password=password, email=email)
    UserProfile.objects.update_or_create(  # type: ignore[attr-defined]
        user=user,
        defaults={'display_name': display_name},
    )

    refresh = RefreshToken.for_user(user)
    display_name = display_name or username
    return Response(
        {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff,
                'display_name': display_name,
            },
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)  # type: ignore[attr-defined]
    return Response(UserProfileSerializer(profile).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # 必须登录才能查看个人档案
def archives_view(request):
    uid = str(request.user.id) if request.user.is_authenticated else None
    query = (request.query_params.get('q') or '').strip().lower()
    start = request.query_params.get('start')
    end = request.query_params.get('end')

    # 未登录用户不显示任何记录
    if not uid:
        return Response({
            'consult_records': [],
            'wellness_archives': [],
            'tongue_archives': [],
        })

    consult_items = []

    # 查询多智能体问诊会话（ConsultationSession）- 只查询当前用户的会话
    debug_info = {
        'uid': uid,
        'total_sessions': 0,
        'user_id_sessions': 0,
        'empty_user_id_sessions': 0,
        'agent_sessions_count': 0,
    }
    try:
        from apps.agents.models import ConsultationSession
        from django.db.models import Q
        
        # 调试：获取所有ConsultationSession记录
        all_sessions = ConsultationSession.objects.all()
        debug_info['total_sessions'] = all_sessions.count()
        debug_info['user_id_sessions'] = ConsultationSession.objects.filter(user_id=uid).count()
        debug_info['empty_user_id_sessions'] = ConsultationSession.objects.filter(user_id='').count()
        
        # 查询用户的所有问诊会话（包括未完成的）
        # 重要：移除严格的过滤条件，以显示所有会话
        agent_sessions = ConsultationSession.objects.filter(
            Q(user_id=uid) | Q(user_id='')  # 包含当前用户的会话和匿名会话
        ).order_by('-created_at')[:100]
        debug_info['agent_sessions_count'] = agent_sessions.count()
        
        for session in agent_sessions:
            # 从state_data中提取数据
            state_data = session.state_data or {}
            observation = state_data.get('observation', {})
            
            item = {
                'session_id': session.session_id,
                'title': session.chief_complaint or state_data.get('chief_complaint', '') or '问诊记录',
                'create_time': session.created_at,
                'application_id': 'tcm-agent',
                'current_stage': session.current_stage,
                'is_high_risk': session.is_high_risk,
                'chief_complaint': session.chief_complaint or state_data.get('chief_complaint', ''),
                'primary_syndrome': session.primary_syndrome or state_data.get('primary_syndrome', ''),
                'symptoms': [],
                'observation': observation,
            }
            
            # 从state_data中提取症状
            symptoms = state_data.get('symptoms', [])
            if symptoms:
                item['symptoms'] = [s.get('name', '') for s in symptoms if s.get('name')]
            
            # 过滤
            haystack = f"{item.get('title', '')} {item.get('chief_complaint', '')} {item.get('primary_syndrome', '')}".lower()
            if not query or query in haystack:
                consult_items.append(item)
    except Exception as e:
        print(f"Error loading agent sessions: {e}")
        debug_info['error'] = str(e)

    # 按时间排序
    consult_items.sort(key=lambda x: x.get('create_time', ''), reverse=True)

    wellness = WellnessArchive.objects.filter(user=request.user).order_by('-create_time')[:50] if request.user.is_authenticated else []  # type: ignore[attr-defined]
    tongues = TongueAnalysisArchive.objects.filter(user=request.user).order_by('-create_time')[:50] if request.user.is_authenticated else []  # type: ignore[attr-defined]

    return Response(
        {
            'consult_records': consult_items,
            'wellness_archives': WellnessArchiveSerializer(wellness, many=True).data if wellness else [],
            'tongue_archives': TongueAnalysisArchiveSerializer(tongues, many=True).data if tongues else [],
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_wellness_archive(request):
    constitution = request.data.get('constitution', '')
    cycle_days = int(request.data.get('cycle_days', 7))
    source_syndrome = request.data.get('source_syndrome', '')
    plan_json = request.data.get('plan_json', {})

    if not constitution or not isinstance(plan_json, dict):
        return Response({'detail': '参数不完整'}, status=status.HTTP_400_BAD_REQUEST)

    item = WellnessArchive.objects.create(  # type: ignore[attr-defined]
        user=request.user,
        constitution=constitution,
        cycle_days=cycle_days,
        source_syndrome=source_syndrome,
        plan_json=plan_json,
    )
    return Response(WellnessArchiveSerializer(item).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_tongue_archive(request):
    analysis_json = request.data.get('analysis_json', {})
    session_id = request.data.get('session_id', '')
    image_name = request.data.get('image_name', '')

    if not isinstance(analysis_json, dict):
        return Response({'detail': 'analysis_json格式错误'}, status=status.HTTP_400_BAD_REQUEST)

    item = TongueAnalysisArchive.objects.create(  # type: ignore[attr-defined]
        user=request.user,
        session_id=session_id,
        image_name=image_name,
        analysis_json=analysis_json,
    )
    return Response(TongueAnalysisArchiveSerializer(item).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_consult_archive(request):
    session_id = request.data.get('session_id', '')
    if not session_id:
        return Response({'detail': 'session_id不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    ConsultArchive.objects.update_or_create(  # type: ignore[attr-defined]
        user=request.user,
        session_id=session_id,
        defaults={
            'title': request.data.get('title', '问诊会话'),
            'current_stage': request.data.get('current_stage', 'inquiry'),
            'latest_question': request.data.get('latest_question', ''),
            'latest_answer': request.data.get('latest_answer', ''),
            'is_high_risk': bool(request.data.get('is_high_risk', False)),
        },
    )
    item = ConsultArchive.objects.get(user=request.user, session_id=session_id)  # type: ignore[attr-defined]
    return Response(ConsultArchiveSerializer(item).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_wellness_checkin(request):
    """保存养生计划打卡记录"""
    date = request.data.get('date', '')
    constitution = request.data.get('constitution', '')
    completed_items = request.data.get('completed_items', [])
    total_items = request.data.get('total_items', 0)
    energy_level = request.data.get('energy_level', 3)
    sleep_quality = request.data.get('sleep_quality', 3)
    mood_score = request.data.get('mood_score', 3)

    if not date:
        return Response({'detail': 'date不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    # 保存到数据库（如果模型存在的话）
    # 目前使用 WellnessArchive 模型存储
    from apps.users.models import WellnessArchive
    
    completion_rate = len(completed_items) / total_items if total_items > 0 else 0
    
    # 将打卡数据存储到养生计划档案中
    checkin_data = {
        'date': date,
        'constitution': constitution,
        'completed_items': completed_items,
        'total_items': total_items,
        'completion_rate': round(completion_rate, 2),
        'energy_level': energy_level,
        'sleep_quality': sleep_quality,
        'mood_score': mood_score,
    }

    # 获取或创建今日的养生计划档案
    from datetime import datetime
    try:
        today_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        today_date = datetime.now().date()

    # 查找最近的养生计划档案并更新打卡数据
    wellness_archive = WellnessArchive.objects.filter(  # type: ignore[attr-defined]
        user=request.user
    ).order_by('-create_time').first()

    if wellness_archive:
        # 更新现有档案的打卡数据
        if not wellness_archive.plan_json:
            wellness_archive.plan_json = {}
        wellness_archive.plan_json['checkins'] = wellness_archive.plan_json.get('checkins', {})
        wellness_archive.plan_json['checkins'][date] = checkin_data
        wellness_archive.save()

    return Response({
        'success': True,
        'message': f'{date} 打卡成功',
        'completion_rate': round(completion_rate, 2),
        'encouragement': '打卡成功！继续坚持 💪'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_stats_view(request):
    if not request.user.is_staff:
        return Response({'detail': '没有权限访问'}, status=status.HTTP_403_FORBIDDEN)
    return Response({'registeredUserCount': User.objects.filter(is_active=True).count()})
