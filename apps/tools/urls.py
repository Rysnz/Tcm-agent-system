from django.urls import path
from apps.tools import views

urlpatterns = [
    path('tool/', views.ToolViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('tool/<uuid:pk>/', views.ToolViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    path('mcp/', views.MCPToolViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('call/', views.ToolCallView.as_view()),
]
