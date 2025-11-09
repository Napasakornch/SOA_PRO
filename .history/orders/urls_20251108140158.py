from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')

# URLs หลักจาก router
urlpatterns = [
    path('', include(router.urls)),
]

# Custom URLs สำหรับ actions พิเศษ
custom_urlpatterns = [
    # User orders - ดูคำสั่งซื้อของผู้ใช้
    path('user-orders/', OrderViewSet.as_view({'get': 'user_orders'}), name='user-orders'),
    
    # Seller orders - ดูคำสั่งซื้อสำหรับผู้ขาย (เพิ่มใหม่)
    path('seller-orders/', OrderViewSet.as_view({'get': 'seller_orders'}), name='seller-orders'),
    
    # Order statistics - สถิติคำสั่งซื้อ
    path('stats/', OrderViewSet.as_view({'get': 'stats'}), name='order-stats'),
]

urlpatterns += custom_urlpatterns