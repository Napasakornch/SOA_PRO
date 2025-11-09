from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')  # เพิ่ม basename

urlpatterns = [
    path('', include(router.urls)),
]