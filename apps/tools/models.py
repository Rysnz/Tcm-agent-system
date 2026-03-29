from django.db import models
from apps.common.models import BaseModel

class Tool(BaseModel):
    name = models.CharField(max_length=128, verbose_name='工具名称')
    desc = models.TextField(verbose_name='工具描述', null=True, blank=True)
    tool_type = models.CharField(max_length=32, verbose_name='工具类型')
    tool_config = models.JSONField(verbose_name='工具配置', default=dict)
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    is_system = models.BooleanField(default=False, verbose_name='是否系统工具')

    class Meta:
        db_table = 'tcm_tool'
        verbose_name = '工具'
        verbose_name_plural = verbose_name

class MCPTool(BaseModel):
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, verbose_name='工具')
    mcp_server_url = models.CharField(max_length=512, verbose_name='MCP服务器地址')
    mcp_config = models.JSONField(verbose_name='MCP配置', default=dict)
    tool_schema = models.JSONField(verbose_name='工具Schema', default=dict)

    class Meta:
        db_table = 'tcm_mcp_tool'
        verbose_name = 'MCP工具'
        verbose_name_plural = verbose_name
