from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.chat import views

router = DefaultRouter()
router.register(r'session', views.ChatSessionViewSet)
router.register(r'message', views.ChatMessageViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('speech_to_text/', views.SpeechToTextView.as_view()),
    path('', views.ChatView.as_view()),  # 支持旧的URL路径
    path('chat/', views.ChatView.as_view()),  # 支持旧的URL路径
    path('stream/', views.ChatStreamView.as_view()),
    path('upload_file/', views.FileUploadView.as_view()),
    path('get_file/<uuid:file_id>/', views.FileGetView.as_view()),
    path('message/<uuid:message_id>/rate/', views.MessageSatisfactionView.as_view()),
]
