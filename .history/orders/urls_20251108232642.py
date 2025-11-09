from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, seller_dashboard, update_order_status, update_order, update_order_quantity

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
    
    # Seller orders - ดูคำสั่งซื้อสำหรับผู้ขาย
    path('seller-orders/', OrderViewSet.as_view({'get': 'seller_orders'}), name='seller-orders'),
    
    # Order statistics - สถิติคำสั่งซื้อ
    path('stats/', OrderViewSet.as_view({'get': 'stats'}), name='order-stats'),
    
    # Seller Dashboard - HTML page สำหรับผู้ขาย
    path('seller/dashboard/', seller_dashboard, name='seller_dashboard'),
    
    # Update order status - สำหรับผู้ขาย
    path('seller/orders/<int:order_id>/update-status/', update_order_status, name='update_order_status'),
    
    # Update order (แก้ไขทั้งหมด) - สำหรับผู้ขาย (เพิ่มใหม่)
    path('seller/orders/<int:order_id>/update/', update_order, name='update_order'),
    
    # Update order quantity (แก้ไขจำนวนอย่างรวดเร็ว) - สำหรับผู้ขาย (เพิ่มใหม่)
    path('seller/orders/<int:order_id>/update-quantity/', update_order_quantity, name='update_order_quantity'),
]

urlpatterns += custom_urlpatterns