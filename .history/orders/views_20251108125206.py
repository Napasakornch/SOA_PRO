from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .serializers import OrderSerializer

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return Order.objects.all().select_related('user', 'pet')
            return Order.objects.filter(user=self.request.user).select_related('pet')
        return Order.objects.none()
    
    def perform_create(self, serializer):
        """Auto assign user และ validate ข้อมูล"""
        if self.request.user.is_authenticated:
            # ตรวจสอบว่ามีข้อมูลการจัดส่งครบถ้วน
            delivery_method = serializer.validated_data.get('delivery_method', 'pickup')
            recipient_name = serializer.validated_data.get('recipient_name', '')
            
            if not recipient_name:
                # ถ้าไม่มีชื่อผู้รับ ให้ใช้ชื่อ user
                recipient_name = self.request.user.get_full_name() or self.request.user.username
                serializer.validated_data['recipient_name'] = recipient_name
            
            serializer.save(user=self.request.user)
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You must be logged in to create an order.")
    
    @action(detail=False, methods=['get'])
    def user_orders(self, request):
        """ดึงคำสั่งซื้อของผู้ใช้"""
        if not request.user.is_authenticated:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You must be logged in to view orders.")
            
        if request.user.is_staff and 'user_id' in request.GET:
            orders = Order.objects.filter(user_id=request.GET['user_id']).select_related('pet')
        else:
            orders = self.get_queryset()
        
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """ยกเลิกคำสั่งซื้อ"""
        order = self.get_object()
        
        # ตรวจสอบสิทธิ์ (เฉพาะเจ้าของหรือ staff)
        if order.user != request.user and not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only cancel your own orders.")
        
        if order.status == 'pending':
            order.status = 'cancelled'
            order.save()
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        else:
            return Response(
                {"error": "Cannot cancel order that is not pending"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        """อัพเดทสถานะคำสั่งซื้อ (สำหรับ staff)"""
        if not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only staff can update order status.")
        
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {"error": "Invalid status"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """สถิติคำสั่งซื้อ"""
        if not request.user.is_authenticated:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You must be logged in to view stats.")
        
        if request.user.is_staff:
            # Staff เห็นสถิติทั้งหมด
            total_orders = Order.objects.count()
            pending_orders = Order.objects.filter(status='pending').count()
            completed_orders = Order.objects.filter(status='completed').count()
            cancelled_orders = Order.objects.filter(status='cancelled').count()
        else:
            # User ธรรมดาเห็นเฉพาะของตัวเอง
            total_orders = Order.objects.filter(user=request.user).count()
            pending_orders = Order.objects.filter(user=request.user, status='pending').count()
            completed_orders = Order.objects.filter(user=request.user, status='completed').count()
            cancelled_orders = Order.objects.filter(user=request.user, status='cancelled').count()
        
        return Response({
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'cancelled_orders': cancelled_orders,
        })
        
        