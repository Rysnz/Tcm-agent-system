from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . import views
from .models import Application

# 直接返回应用列表，绕过权限检查
@csrf_exempt
def application_list(request):
    """直接返回应用列表，绕过权限检查"""
    if request.method == 'GET':
        applications = Application.objects.filter(is_delete=False)
        result = []
        for app in applications:
            result.append({
                'id': str(app.id),
                'name': app.name,
                'desc': app.desc,
                'icon': app.icon,
                'user_id': str(app.user.id) if app.user else None,
                'work_flow': app.work_flow,
                'model_config': app.model_config,
                'knowledge_bases': app.knowledge_bases,
                'tools': app.tools,
                'prompt_template': app.prompt_template,
                'prompt_template_type': app.prompt_template_type,
                'similarity_threshold': app.similarity_threshold,
                'top_k': app.top_k,
                'system_prompt': app.system_prompt,
                'is_active': app.is_active,
                'enable_file_upload': app.enable_file_upload
            })
        return JsonResponse({'count': len(result), 'next': None, 'previous': None, 'results': result})
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def application_detail(request, pk):
    """直接返回应用详情，绕过权限检查"""
    try:
        app = Application.objects.get(id=pk, is_delete=False)
        return JsonResponse({
            'id': str(app.id),
            'name': app.name,
            'desc': app.desc,
            'icon': app.icon,
            'user_id': str(app.user.id) if app.user else None,
            'work_flow': app.work_flow,
            'model_config': app.model_config,
            'knowledge_bases': app.knowledge_bases,
            'tools': app.tools,
            'prompt_template': app.prompt_template,
            'prompt_template_type': app.prompt_template_type,
            'similarity_threshold': app.similarity_threshold,
            'top_k': app.top_k,
            'system_prompt': app.system_prompt,
            'is_active': app.is_active,
            'enable_file_upload': app.enable_file_upload
        })
    except Application.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

@csrf_exempt
def application_stats(request):
    """直接返回应用统计数据，绕过权限检查"""
    from datetime import datetime, timedelta
    from django.db.models import Sum
    from apps.chat.models import ChatMessage
    
    # 获取查询参数
    time_range = request.GET.get('timeRange', '7')
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    
    # 计算日期范围
    if time_range == 'custom' and start_date and end_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            # 将结束日期设置为当天的23:59:59
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
        except ValueError:
            return JsonResponse({'error': 'Invalid date format, please use YYYY-MM-DD'}, status=400)
    else:
        # 根据timeRange计算日期范围
        end_datetime = datetime.now()
        if time_range == '7':
            start_datetime = end_datetime - timedelta(days=7)
        elif time_range == '30':
            start_datetime = end_datetime - timedelta(days=30)
        elif time_range == '90':
            start_datetime = end_datetime - timedelta(days=90)
        elif time_range == '180':
            start_datetime = end_datetime - timedelta(days=180)
        else:
            start_datetime = end_datetime - timedelta(days=7)
    
    # 计算用户总数（通过session关联获取user_id去重）
    user_count = ChatMessage.objects.filter(
        create_time__gte=start_datetime,
        create_time__lte=end_datetime,
        session__user_id__isnull=False
    ).values('session__user_id').distinct().count()
    
    # 计算提问次数（用户消息）
    question_count = ChatMessage.objects.filter(
        create_time__gte=start_datetime,
        create_time__lte=end_datetime,
        role='user'
    ).count()
    
    # 计算tokens总数（所有消息）
    tokens_count = ChatMessage.objects.filter(
        create_time__gte=start_datetime,
        create_time__lte=end_datetime
    ).aggregate(Sum('tokens'))['tokens__sum'] or 0
    
    # 计算赞同和反对数量
    liked_count = ChatMessage.objects.filter(
        create_time__gte=start_datetime,
        create_time__lte=end_datetime,
        role='assistant',
        satisfaction=1
    ).count()
    disliked_count = ChatMessage.objects.filter(
        create_time__gte=start_datetime,
        create_time__lte=end_datetime,
        role='assistant',
        satisfaction=0
    ).count()
    
    # 生成每日统计数据的函数
    def get_daily_stats():
        """获取每日统计数据"""
        daily_stats = {}
        
        # 获取所有消息来计算统计数据
        messages = ChatMessage.objects.filter(
            create_time__gte=start_datetime,
            create_time__lte=end_datetime
        )
        
        # 按日期分组
        for msg in messages:
            date_key = msg.create_time.strftime('%m-%d')
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'user_count': set(),
                    'question_count': 0,
                    'tokens': 0,
                    'satisfied_count': 0,
                    'dissatisfied_count': 0
                }
            
            # 统计用户数（通过session关联获取user_id）
            if msg.session and msg.session.user_id:
                daily_stats[date_key]['user_count'].add(str(msg.session.user_id))
            
            # 统计提问次数（用户消息）
            if msg.role == 'user':
                daily_stats[date_key]['question_count'] += 1
            
            # 统计tokens（所有消息）
            daily_stats[date_key]['tokens'] += msg.tokens or 0
        
        # 获取用户满意度数据（用户对AI回复的评价）
        satisfaction_messages = ChatMessage.objects.filter(
            create_time__gte=start_datetime,
            create_time__lte=end_datetime,
            role='assistant',
            satisfaction__in=[0, 1]
        )
        
        for msg in satisfaction_messages:
            date_key = msg.create_time.strftime('%m-%d')
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'user_count': set(),
                    'question_count': 0,
                    'tokens': 0,
                    'satisfied_count': 0,
                    'dissatisfied_count': 0
                }
            
            if msg.satisfaction == 1:
                daily_stats[date_key]['satisfied_count'] += 1
            elif msg.satisfaction == 0:
                daily_stats[date_key]['dissatisfied_count'] += 1
        
        return daily_stats
    
    # 计算图表数据
    chart_days = 7
    if time_range == '30':
        chart_days = 30
    elif time_range == '90':
        chart_days = 90
    elif time_range == '180':
        chart_days = 180
    
    # 生成日期列表
    dates = []
    for i in range(chart_days, 0, -1):
        date = end_datetime - timedelta(days=i)
        dates.append(date.strftime('%m-%d'))
    
    # 获取每日统计数据
    daily_stats = get_daily_stats()
    
    # 生成图表值
    def get_chart_values(stats_dict, field, dates_list):
        values = []
        for date in dates_list:
            if date in stats_dict:
                if field == 'user_count':
                    values.append(len(stats_dict[date]['user_count']))
                elif field == 'question_count':
                    values.append(stats_dict[date]['question_count'])
                elif field == 'tokens':
                    values.append(stats_dict[date]['tokens'])
                elif field == 'liked':
                    values.append(stats_dict[date]['satisfied_count'])
                elif field == 'disliked':
                    values.append(stats_dict[date]['dissatisfied_count'])
                else:
                    values.append(0)
            else:
                if field in ['liked', 'disliked']:
                    values.append(0)
                else:
                    values.append(0)
        return values
    
    user_values = get_chart_values(daily_stats, 'user_count', dates)
    question_values = get_chart_values(daily_stats, 'question_count', dates)
    tokens_values = get_chart_values(daily_stats, 'tokens', dates)
    liked_values = get_chart_values(daily_stats, 'liked', dates)
    disliked_values = get_chart_values(daily_stats, 'disliked', dates)
    
    # 构建响应数据
    response_data = {
        'stats': {
            'userCount': user_count,
            'questionCount': question_count,
            'tokensCount': tokens_count,
            'likedCount': liked_count,
            'dislikedCount': disliked_count
        },
        'charts': [
            {
                'name': '用户总数',
                'values': user_values,
                'dates': dates,
                'color': '#409eff',
                'icon': 'User'
            },
            {
                'name': '提问次数',
                'values': question_values,
                'dates': dates,
                'color': '#67c23a',
                'icon': 'Message'
            },
            {
                'name': 'Tokens 总数',
                'values': tokens_values,
                'dates': dates,
                'color': '#e6a23c',
                'icon': 'Document'
            },
            {
                'name': '用户满意度',
                'likedValues': liked_values,
                'dislikedValues': disliked_values,
                'dates': dates
            }
        ]
    }
    
    response = JsonResponse(response_data)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

urlpatterns = [
    # 绕过权限的路由，放在最前面以确保被正确匹配
    path('no-auth/', application_list),
    path('no-auth/<uuid:pk>/', application_detail),
    path('stats/', application_stats),
    
    # 默认路由，使用ViewSet
    path('', views.ApplicationViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<uuid:pk>/', views.ApplicationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    path('<uuid:pk>/create_api_key/', views.ApplicationViewSet.as_view({'post': 'create_api_key'})),
    path('<uuid:pk>/nodes/', views.ApplicationViewSet.as_view({'get': 'nodes', 'post': 'nodes'})),
    path('<uuid:pk>/edges/', views.ApplicationViewSet.as_view({'get': 'edges', 'post': 'edges'})),
    path('<uuid:pk>/knowledge_bases/', views.ApplicationViewSet.as_view({'get': 'knowledge_bases'})),
    path('<uuid:pk>/execute/', views.ApplicationViewSet.as_view({'post': 'execute'})),
    path('<uuid:pk>/nodes/<uuid:node_id>/', views.ApplicationViewSet.as_view({'get': 'nodes', 'put': 'nodes', 'delete': 'nodes'})),
    path('<uuid:pk>/edges/<uuid:edge_id>/', views.ApplicationViewSet.as_view({'get': 'edges', 'put': 'edges', 'delete': 'edges'})),
    
    # API视图路由
    path('workflow/execute/', views.WorkflowExecuteView.as_view()),
    path('workflow/validate/', views.WorkflowValidateView.as_view()),
    path('workflow/save/', views.WorkflowSaveView.as_view()),
]
