from django.urls import path
from apps.knowledge import views

urlpatterns = [
    path('knowledge_base/', views.KnowledgeBaseViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('knowledge_base/<uuid:pk>/', views.KnowledgeBaseViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    path('document/', views.DocumentViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('document/<uuid:pk>/', views.DocumentViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    path('upload/', views.DocumentUploadView.as_view()),
    path('search/', views.KnowledgeSearchView.as_view()),
]
