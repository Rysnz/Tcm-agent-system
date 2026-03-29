from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.tools.models import Tool, MCPTool
from apps.tools.serializers import ToolSerializer, MCPToolSerializer
from apps.common.permissions import IsStaffUser

class ToolViewSet(viewsets.ModelViewSet):
    queryset = Tool.objects.filter(is_delete=False)
    serializer_class = ToolSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]

class MCPToolViewSet(viewsets.ModelViewSet):
    queryset = MCPTool.objects.filter(is_delete=False)
    serializer_class = MCPToolSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]

class ToolCallView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]
    
    def post(self, request):
        tool_name = request.data.get('tool_name')
        params = request.data.get('params', {})
        
        if not tool_name:
            return Response(
                {'error': 'tool_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.application.flow.tcm_tools import TCMTools
        tools = TCMTools()
        
        try:
            result = tools.call(tool_name, params)
            return Response({
                'tool_name': tool_name,
                'result': result
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
