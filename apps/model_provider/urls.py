from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.model_provider.views import (
    ModelConfigViewSet, ModelProviderView,
    ModelTypeView, ModelListView,
    ModelCredentialView, ModelParamsFormView
)

# 创建默认路由
router = DefaultRouter()
router.register(r'model-config', ModelConfigViewSet, basename='model-config')

# 定义API路由
urlpatterns = [
    # 模型配置相关路由
    path('', include(router.urls)),
    
    # 模型提供商相关路由
    path('providers/', ModelProviderView.as_view(), name='model-providers'),
    path('model-types/', ModelTypeView.as_view(), name='model-types'),
    path('model-list/', ModelListView.as_view(), name='model-list'),
    path('validate-credential/', ModelCredentialView.as_view(), name='validate-credential'),
    path('model-params-form/', ModelParamsFormView.as_view(), name='model-params-form'),
]