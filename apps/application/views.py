from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum
from apps.application.models import Application, WorkflowNode, WorkflowEdge
from apps.application.serializers import ApplicationSerializer, WorkflowNodeSerializer, WorkflowEdgeSerializer
from apps.application.flow.workflow_manage import WorkflowManager

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.filter(is_delete=False)
    serializer_class = ApplicationSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def create_api_key(self, request, pk=None):
        """创建API密钥"""
        # 已移除API密钥功能
        return Response({'error': 'API key functionality has been removed'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get', 'post'])
    def nodes(self, request, pk=None):
        """获取或创建工作流节点"""
        application = self.get_object()
        
        if request.method == 'GET':
            nodes = WorkflowNode.objects.filter(application_id=application.id)
            serializer = WorkflowNodeSerializer(nodes, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            serializer = WorkflowNodeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(application_id=application.id)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'post'])
    def edges(self, request, pk=None):
        """获取或创建工作流边"""
        application = self.get_object()
        
        if request.method == 'GET':
            edges = WorkflowEdge.objects.filter(application_id=application.id)
            serializer = WorkflowEdgeSerializer(edges, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            serializer = WorkflowEdgeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(application_id=application.id)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def associate_knowledge_base(self, request, pk=None):
        """关联知识库到应用"""
        application = self.get_object()
        knowledge_base_id = request.data.get('knowledge_base_id')
        
        if not knowledge_base_id:
            return Response(
                {'error': 'knowledge_base_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新应用的知识库关联
        if application.knowledge_bases is None:
            application.knowledge_bases = []
        
        if knowledge_base_id not in application.knowledge_bases:
            application.knowledge_bases.append(knowledge_base_id)
            application.save()
        
        return Response({'message': 'Knowledge base associated successfully'})
    
    @action(detail=True, methods=['post'])
    def disassociate_knowledge_base(self, request, pk=None):
        """从应用解除知识库关联"""
        application = self.get_object()
        knowledge_base_id = request.data.get('knowledge_base_id')
        
        if not knowledge_base_id:
            return Response(
                {'error': 'knowledge_base_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新应用的知识库关联
        if application.knowledge_bases and knowledge_base_id in application.knowledge_bases:
            application.knowledge_bases.remove(knowledge_base_id)
            application.save()
        
        return Response({'message': 'Knowledge base disassociated successfully'})
    
    @action(detail=True, methods=['get'])
    def knowledge_bases(self, request, pk=None):
        """获取应用关联的知识库"""
        from apps.knowledge.models import KnowledgeBase
        application = self.get_object()
        
        knowledge_bases = []
        if application.knowledge_bases:
            knowledge_bases = KnowledgeBase.objects.filter(
                id__in=application.knowledge_bases, 
                is_delete=False
            )
        
        from apps.knowledge.serializers import KnowledgeBaseSerializer
        serializer = KnowledgeBaseSerializer(knowledge_bases, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        application = self.get_object()
        input_data = request.data.get('input_data', {})
        
        workflow_manager = WorkflowManager(str(application.id))
        result = workflow_manager.execute(input_data)
        
        return Response(result)

class WorkflowExecuteView(APIView):
    
    def post(self, request):
        application_id = request.data.get('application_id')
        input_data = request.data.get('input_data', {})
        
        if not application_id:
            return Response(
                {'error': 'application_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        workflow_manager = WorkflowManager(application_id)
        result = workflow_manager.execute(input_data)
        
        return Response(result)

class WorkflowValidateView(APIView):
    
    def post(self, request):
        application_id = request.data.get('application_id')
        
        if not application_id:
            return Response(
                {'error': 'application_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        workflow_manager = WorkflowManager(application_id)
        validation_result = workflow_manager.validate_workflow()
        
        return Response(validation_result)

class WorkflowSaveView(APIView):
    
    def post(self, request):
        import json
        application_id = request.data.get('application_id')
        nodes = request.data.get('nodes', [])
        edges = request.data.get('edges', [])
        
        if not application_id:
            return Response(
                {'error': 'application_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            workflow_data = {
                'nodes': nodes,
                'edges': edges
            }
            
            application = Application.objects.get(id=application_id)
            application.work_flow = json.dumps(workflow_data)
            application.save()
            
            return Response({
                'status': 'success',
                'message': '工作流保存成功'
            })
        except Application.DoesNotExist:
            return Response(
                {'error': '应用不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'保存失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ApplicationStatsView(APIView):
    """获取应用统计数据"""
    
    def get(self, request):
        """
        获取应用统计数据
        支持的查询参数：
        - timeRange: 时间范围，可选值：7, 30, 90, 180, custom
        - startDate: 开始日期（当timeRange=custom时必填）
        - endDate: 结束日期（当timeRange=custom时必填）
        """
        from datetime import datetime, timedelta
        from django.db.models.functions import TruncDate
        from apps.chat.models import ChatMessage
        
        # 获取查询参数
        time_range = request.query_params.get('timeRange', '7')
        start_date = request.query_params.get('startDate')
        end_date = request.query_params.get('endDate')
        
        # 计算日期范围
        if time_range == 'custom' and start_date and end_date:
            try:
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                # 将结束日期设置为当天的23:59:59
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format, please use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
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
                    'name': '赞同数',
                    'values': liked_values,
                    'dates': dates,
                    'color': '#13ce66',
                    'icon': 'Star'
                },
                {
                    'name': '反对数',
                    'values': disliked_values,
                    'dates': dates,
                    'color': '#f56c6c',
                    'icon': 'Star'
                }
            ]
        }
        
        return Response(response_data)
