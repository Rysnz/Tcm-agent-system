from django.urls import path
from apps.knowledge import views

urlpatterns = [
    path('knowledge_base/', views.KnowledgeBaseViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('knowledge_base/<uuid:pk>/', views.KnowledgeBaseViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    path('knowledge_base/<uuid:pk>/stats/', views.KnowledgeBaseViewSet.as_view({'get': 'stats'})),
    path('document/', views.DocumentViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('document/<uuid:pk>/', views.DocumentViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    path('document/<uuid:pk>/paragraphs/', views.DocumentViewSet.as_view({'get': 'paragraphs'})),
    path('document/<uuid:pk>/reprocess/', views.DocumentViewSet.as_view({'post': 'reprocess'})),
    path('upload/', views.DocumentUploadView.as_view()),
    path('search/', views.KnowledgeSearchView.as_view()),
]
