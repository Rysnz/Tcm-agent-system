from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.common.models import BaseModel
from .models import Application, WorkflowNode, WorkflowEdge
from .serializers import ApplicationSerializer, WorkflowNodeSerializer, WorkflowEdgeSerializer


class ApplicationAPIKey(BaseModel):
    name = models.CharField(max_length=64, verbose_name='API密钥名称')
    api_key = models.CharField(max_length=256, unique=True, verbose_name='API密钥')
    enabled = models.BooleanField(default=True, verbose_name='是否启用')
    usage_count = models.IntegerField(default=0, verbose_name='使用次数')
    application = models.ForeignKey(Application, on_delete=models.CASCADE, verbose_name='关联应用')
    
    class Meta:
        db_table = 'tcm_application_api_key'
        verbose_name = '应用API密钥'
        verbose_name_plural = '应用API密钥'


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """获取当前用户有权访问的应用列表"""
        user = self.request.user
        if user.is_staff:  # 管理员用户可以访问所有应用
            return Application.objects.filter(is_delete=False)
        else:  # 普通用户只能访问自己的应用
            return Application.objects.filter(is_delete=False, user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)
        
    @action(detail=True, methods=['post'])
    def create_api_key(self, request, pk=None):
        application = self.get_object()
        import uuid
        api_key = f'sk_{uuid.uuid4().hex}'
        ApplicationAPIKey.objects.create(
            name=f'API Key for {application.name}',
            api_key=api_key,
            application=application
        )
        return Response({'api_key': api_key}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get', 'post'])
    def nodes(self, request, pk=None):
        application = self.get_object()
        
        if request.method == 'GET':
            nodes = WorkflowNode.objects.filter(application=application, is_delete=False)
            serializer = WorkflowNodeSerializer(nodes, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            data = request.data
            nodes = data.get('nodes', [])
            for node in nodes:
                WorkflowNode.objects.create(
                    application=application,
                    node_id=node['node_id'],
                    node_type=node['node_type'],
                    node_data=node['node_data'],
                    position=node['position']
                )
            return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get', 'post'])
    def edges(self, request, pk=None):
        application = self.get_object()
        
        if request.method == 'GET':
            edges = WorkflowEdge.objects.filter(application=application, is_delete=False)
            serializer = WorkflowEdgeSerializer(edges, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            data = request.data
            edges = data.get('edges', [])
            for edge in edges:
                WorkflowEdge.objects.create(
                    application=application,
                    source_node=edge['source_node'],
                    target_node=edge['target_node'],
                    edge_data=edge['edge_data']
                )
            return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
