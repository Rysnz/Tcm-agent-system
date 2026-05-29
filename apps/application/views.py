from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import datetime, timedelta, time
from apps.application.models import Application, WorkflowNode, WorkflowEdge
from apps.application.serializers import ApplicationSerializer, WorkflowNodeSerializer, WorkflowEdgeSerializer
from apps.application.flow.workflow_manage import WorkflowManager
from apps.common.permissions import IsStaffUser, IsStaffOrReadOnly

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application._default_manager.filter(is_delete=False).order_by('-create_time')
    serializer_class = ApplicationSerializer
    permission_classes = [IsStaffOrReadOnly]
    
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
    permission_classes = [IsAuthenticated, IsStaffUser]
    
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
    permission_classes = [IsAuthenticated, IsStaffUser]
    
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
    permission_classes = [IsAuthenticated, IsStaffUser]
    
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
            
            application = Application._default_manager.get(id=application_id)
            application.work_flow = json.dumps(workflow_data)
            application.save()
            
            return Response({
                'status': 'success',
                'message': '工作流保存成功'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """
        获取应用统计数据
        """
        from datetime import datetime, timedelta
        
        # 返回空统计数据（新系统暂无统计功能）
        # TODO: 基于 ConsultationSession 实现统计功能
        return Response({
            'user_count': 0,
            'question_count': 0,
            'tokens_count': 0,
            'liked_count': 0,
            'disliked_count': 0,
            'daily_stats': {},
            'message': '统计数据功能正在迁移中'
        })


class ApplicationStatsView(APIView):
    """获取应用统计数据"""
    permission_classes = [IsAuthenticated, IsStaffUser]

    @classmethod
    def _extract_message_tokens(cls, message: dict) -> int:
        """仅读取消息内真实记录的 token 信息。"""
        for key in ('tokens', 'token_count', 'total_tokens'):
            value = message.get(key)
            if isinstance(value, (int, float)) and value > 0:
                return int(value)

        usage = message.get('usage')
        if isinstance(usage, dict):
            total = usage.get('total_tokens')
            if isinstance(total, (int, float)) and total > 0:
                return int(total)

        return 0

    @staticmethod
    def _resolve_date_range(request):
        """解析时间范围参数并返回时区感知时间区间。"""
        time_range = request.query_params.get('timeRange', '7')
        start_date = request.query_params.get('startDate')
        end_date = request.query_params.get('endDate')

        if time_range == 'custom' and start_date and end_date:
            try:
                start_naive = datetime.strptime(start_date, '%Y-%m-%d')
                end_naive = datetime.combine(datetime.strptime(end_date, '%Y-%m-%d').date(), time.max)
                start_datetime = timezone.make_aware(start_naive)
                end_datetime = timezone.make_aware(end_naive)
                return time_range, start_datetime, end_datetime
            except ValueError:
                return None, None, None

        end_datetime = timezone.now()
        if time_range == '30':
            days = 30
        elif time_range == '90':
            days = 90
        elif time_range == '180':
            days = 180
        else:
            days = 7
            time_range = '7'

        start_datetime = end_datetime - timedelta(days=days)
        return time_range, start_datetime, end_datetime

    @staticmethod
    def _build_date_labels(time_range: str, start_datetime, end_datetime):
        """生成图表日期标签（MM-DD）。"""
        if time_range == 'custom':
            total_days = max(1, (end_datetime.date() - start_datetime.date()).days + 1)
            total_days = min(total_days, 180)
            start_date = start_datetime.date()
        else:
            total_days = int(time_range)
            start_date = end_datetime.date() - timedelta(days=total_days - 1)

        labels = []
        for i in range(total_days):
            day = start_date + timedelta(days=i)
            labels.append(day.strftime('%m-%d'))
        return labels

    @staticmethod
    def _stage_label(stage: str) -> str:
        labels = {
            'intake': '主诉采集',
            'inquiry': '追问补充',
            'observation': '望诊采集',
            'syndrome': '辨证分析',
            'recommendation': '调理建议',
            'report': '报告整理',
            'done': '已完成',
        }
        return labels.get(str(stage or '').split('.')[-1].lower(), stage or '未知')

    @staticmethod
    def _percent(numerator: int, denominator: int) -> int:
        if denominator <= 0:
            return 0
        return round(numerator * 100 / denominator)
    
    def get(self, request):
        """
        获取应用统计数据（基于 ConsultationSession 与 AgentExecutionLog 真实聚合）
        """
        from django.contrib.auth.models import User
        from django.db.models import Avg, Count, Q
        from apps.agents.models import AgentExecutionLog, ConsultationSession

        time_range, start_datetime, end_datetime = self._resolve_date_range(request)
        if not time_range:
            return Response(
                {'error': 'Invalid date format, please use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sessions = ConsultationSession._default_manager.filter(
            updated_at__gte=start_datetime,
            updated_at__lte=end_datetime,
            is_archived=False,
        )
        logs = AgentExecutionLog.objects.filter(
            started_at__gte=start_datetime,
            started_at__lte=end_datetime,
        )

        active_user_ids = set()
        total_session_count = 0
        completed_session_count = 0
        report_count = 0
        high_risk_count = 0
        total_question_count = 0
        total_tokens_count = 0
        daily_stats = {}
        stage_distribution = {}
        syndrome_distribution = {}

        for session in sessions.iterator():
            total_session_count += 1
            if session.is_completed:
                completed_session_count += 1
            if session.is_high_risk:
                high_risk_count += 1

            local_updated_at = timezone.localtime(session.updated_at)
            date_key = local_updated_at.strftime('%m-%d')
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'user_ids': set(),
                    'session_count': 0,
                    'completed_count': 0,
                    'high_risk_count': 0,
                    'question_count': 0,
                    'tokens_count': 0,
                    'agent_fail_count': 0,
                }
            daily_stats[date_key]['session_count'] += 1
            if session.is_completed:
                daily_stats[date_key]['completed_count'] += 1
            if session.is_high_risk:
                daily_stats[date_key]['high_risk_count'] += 1

            stage_key = str(session.current_stage or 'unknown').split('.')[-1].lower()
            stage_distribution[stage_key] = stage_distribution.get(stage_key, 0) + 1

            state_data = session.state_data if isinstance(session.state_data, dict) else {}
            messages = state_data.get('messages', [])
            if not isinstance(messages, list):
                messages = []

            question_count = 0
            tokens_count = 0
            for message in messages:
                if not isinstance(message, dict):
                    continue
                if message.get('role') == 'user':
                    question_count += 1
                tokens_count += self._extract_message_tokens(message)

            total_question_count += question_count
            total_tokens_count += tokens_count
            daily_stats[date_key]['question_count'] += question_count
            daily_stats[date_key]['tokens_count'] += tokens_count

            has_report = bool(state_data.get('report_text')) or bool(state_data.get('report_json'))
            if session.is_completed or has_report:
                report_count += 1

            syndrome = session.primary_syndrome or state_data.get('primary_syndrome') or ''
            syndrome = str(syndrome).strip()
            if syndrome:
                syndrome_distribution[syndrome] = syndrome_distribution.get(syndrome, 0) + 1

            user_id = (session.user_id or '').strip()
            if user_id and question_count > 0:
                active_user_ids.add(user_id)
                daily_stats[date_key]['user_ids'].add(user_id)

        for log in logs.filter(success=False).only('started_at').iterator():
            date_key = timezone.localtime(log.started_at).strftime('%m-%d')
            if date_key in daily_stats:
                daily_stats[date_key]['agent_fail_count'] += 1

        date_labels = self._build_date_labels(time_range, start_datetime, end_datetime)
        user_values = [len(daily_stats.get(label, {}).get('user_ids', set())) for label in date_labels]
        session_values = [daily_stats.get(label, {}).get('session_count', 0) for label in date_labels]
        completed_values = [daily_stats.get(label, {}).get('completed_count', 0) for label in date_labels]
        high_risk_values = [daily_stats.get(label, {}).get('high_risk_count', 0) for label in date_labels]
        question_values = [daily_stats.get(label, {}).get('question_count', 0) for label in date_labels]
        tokens_values = [daily_stats.get(label, {}).get('tokens_count', 0) for label in date_labels]
        agent_fail_values = [daily_stats.get(label, {}).get('agent_fail_count', 0) for label in date_labels]

        agent_total = logs.count()
        agent_success = logs.filter(success=True).count()
        agent_duration = logs.filter(duration_ms__isnull=False).aggregate(avg=Avg('duration_ms'))['avg'] or 0
        agent_stats = (
            logs.values('agent_name')
            .annotate(
                total=Count('id'),
                success_count=Count('id', filter=Q(success=True)),
                failed_count=Count('id', filter=Q(success=False)),
                avg_duration_ms=Avg('duration_ms'),
            )
            .order_by('-total', 'agent_name')
        )
        agent_performance = []
        for item in agent_stats:
            total = item['total'] or 0
            success = item['success_count'] or 0
            agent_performance.append({
                'agent': item['agent_name'],
                'total': total,
                'success': success,
                'failed': item['failed_count'] or 0,
                'successRate': self._percent(success, total),
                'avgDurationMs': round(item['avg_duration_ms'] or 0),
            })

        recent_errors = []
        for log in logs.filter(success=False).exclude(error_message='').order_by('-started_at')[:5]:
            recent_errors.append({
                'agent': log.agent_name,
                'stage': self._stage_label(log.stage),
                'message': log.error_message[:160],
                'time': timezone.localtime(log.started_at).strftime('%m-%d %H:%M'),
            })

        stage_items = [
            {
                'stage': key,
                'label': self._stage_label(key),
                'count': value,
                'percent': self._percent(value, total_session_count),
            }
            for key, value in sorted(stage_distribution.items(), key=lambda pair: pair[1], reverse=True)
        ]
        syndrome_items = [
            {'name': key, 'count': value, 'percent': self._percent(value, max(1, report_count))}
            for key, value in sorted(syndrome_distribution.items(), key=lambda pair: pair[1], reverse=True)[:8]
        ]

        response_data = {
            'stats': {
                'registeredUserCount': User.objects.filter(is_active=True).count(),
                'activeUserCount': len(active_user_ids),
                'sessionCount': total_session_count,
                'completedSessionCount': completed_session_count,
                'reportCount': report_count,
                'highRiskCount': high_risk_count,
                'questionCount': total_question_count,
                'tokensCount': total_tokens_count,
                'agentCallCount': agent_total,
                'agentSuccessRate': self._percent(agent_success, agent_total),
                'avgAgentDurationMs': round(agent_duration),
                'avgQuestionsPerSession': round(total_question_count / total_session_count, 1) if total_session_count else 0,
            },
            'charts': [
                {
                    'name': '活跃用户数',
                    'values': user_values,
                    'dates': date_labels,
                    'color': '#409eff',
                    'icon': 'User',
                },
                {
                    'name': '问诊会话',
                    'values': session_values,
                    'dates': date_labels,
                    'color': '#14b8a6',
                    'icon': 'Chat',
                },
                {
                    'name': '提问次数',
                    'values': question_values,
                    'dates': date_labels,
                    'color': '#67c23a',
                    'icon': 'Message',
                },
                {
                    'name': 'Token消耗',
                    'values': tokens_values,
                    'dates': date_labels,
                    'color': '#e6a23c',
                    'icon': 'Document',
                },
                {
                    'name': '完成报告',
                    'values': completed_values,
                    'dates': date_labels,
                    'color': '#8b5cf6',
                    'icon': 'Finished',
                },
                {
                    'name': '高风险提醒',
                    'values': high_risk_values,
                    'dates': date_labels,
                    'color': '#ef4444',
                    'icon': 'Warning',
                },
                {
                    'name': 'Agent失败',
                    'values': agent_fail_values,
                    'dates': date_labels,
                    'color': '#f97316',
                    'icon': 'Connection',
                },
            ],
            'monitor': {
                'generatedAt': timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S'),
                'range': {
                    'start': timezone.localtime(start_datetime).strftime('%Y-%m-%d'),
                    'end': timezone.localtime(end_datetime).strftime('%Y-%m-%d'),
                    'label': f"{timezone.localtime(start_datetime).strftime('%m-%d')} 至 {timezone.localtime(end_datetime).strftime('%m-%d')}",
                },
                'stageDistribution': stage_items,
                'syndromeDistribution': syndrome_items,
                'agentPerformance': agent_performance,
                'recentErrors': recent_errors,
            },
        }

        return Response(response_data)


class ApplicationView(APIView):
    """应用视图"""
    permission_classes = [IsAuthenticated, IsStaffUser]
    
    def get(self, request):
        """
        获取应用统计数据（已更新为使用新的问诊系统）
        支持的查询参数：
        - timeRange: 时间范围，可选值：7, 30, 90, 180, custom
        - startDate: 开始日期（当timeRange=custom时必填）
        - endDate: 结束日期（当timeRange=custom时必填）
        """
        from datetime import datetime, timedelta
        
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
        
        # 返回空统计数据（新系统暂无统计功能）
        # TODO: 基于 ConsultationSession 实现统计功能
        return Response({
            'user_count': 0,
            'question_count': 0,
            'tokens_count': 0,
            'liked_count': 0,
            'disliked_count': 0,
            'daily_stats': {},
            'message': '统计数据功能正在迁移中'
        })
        
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
