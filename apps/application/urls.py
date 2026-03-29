from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.ApplicationStatsView.as_view()),
    
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
