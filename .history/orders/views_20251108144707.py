from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order
from .serializers import OrderSerializer
from users.permissions import IsSellerOrAdminUser  # นำเข้า permissions ใหม่

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return Order.objects.none()
            
        if user.is_admin():
            # Admin เห็นทุกคำสั่งซื้อ
            return Order.objects.all().select_related('user', 'pet')
        elif user.is_seller():
            # Seller เห็นเฉพาะคำสั่งซื้อที่เกี่ยวข้องกับสัตว์เลี้ยงของตัวเอง
            return Order.objects.filter(pet__created_by=user).select_related('user', 'pet')
        else:
            # Customer เห็นเฉพาะคำสั่งซื้อของตัวเอง
            return Order.objects.filter(user=user).select_related('pet')
    
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
            raise PermissionDenied("You must be logged in to create an order.")
    
    @action(detail=False, methods=['get'])
    def user_orders(self, request):
        """ดึงคำสั่งซื้อของผู้ใช้"""
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to view orders.")
            
        if request.user.is_admin() and 'user_id' in request.GET:
            # Admin สามารถดูคำสั่งซื้อของ user อื่นได้
            orders = Order.objects.filter(user_id=request.GET['user_id']).select_related('pet')
        else:
            orders = self.get_queryset()
        
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """ยกเลิกคำสั่งซื้อ"""
        order = self.get_object()
        
        # ตรวจสอบสิทธิ์ (เฉพาะเจ้าของหรือ admin)
        if order.user != request.user and not request.user.is_admin():
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
    
    @action(detail=True, methods=['post'], permission_classes=[IsSellerOrAdminUser])
    def update_status(self, request, pk=None):
        """อัพเดทสถานะคำสั่งซื้อ (สำหรับ seller และ admin)"""
        order = self.get_object()
        
        # สำหรับ seller ตรวจสอบว่าเป็นสัตว์เลี้ยงของตัวเอง
        if request.user.is_seller() and order.pet.created_by != request.user:
            raise PermissionDenied("คุณไม่มีสิทธิ์อัพเดทคำสั่งซื้อนี้")
        
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
    def seller_orders(self, request):
        """ดึงคำสั่งซื้อสำหรับ seller (เฉพาะที่เกี่ยวข้องกับสัตว์เลี้ยงของตัวเอง)"""
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to view orders.")
        
        if request.user.is_seller():
            orders = Order.objects.filter(pet__created_by=request.user).select_related('user', 'pet')
            serializer = self.get_serializer(orders, many=True)
            return Response(serializer.data)
        else:
            raise PermissionDenied("Only sellers can access this endpoint.")
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """สถิติคำสั่งซื้อ"""
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to view stats.")
        
        if request.user.is_admin():
            # Admin เห็นสถิติทั้งหมด
            total_orders = Order.objects.count()
            pending_orders = Order.objects.filter(status='pending').count()
            completed_orders = Order.objects.filter(status='completed').count()
            cancelled_orders = Order.objects.filter(status='cancelled').count()
        elif request.user.is_seller():
            # Seller เห็นสถิติของตัวเอง
            total_orders = Order.objects.filter(pet__created_by=request.user).count()
            pending_orders = Order.objects.filter(pet__created_by=request.user, status='pending').count()
            completed_orders = Order.objects.filter(pet__created_by=request.user, status='completed').count()
            cancelled_orders = Order.objects.filter(pet__created_by=request.user, status='cancelled').count()
        else:
            # Customer เห็นเฉพาะของตัวเอง
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


# เพิ่มฟังก์ชันสำหรับ HTML views
@login_required
def seller_dashboard(request):
    """Dashboard สำหรับผู้ขาย - แสดงคำสั่งซื้อทั้งหมด"""
    if not request.user.is_seller():
        messages.error(request, "คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
        return redirect('home')
    
    # แสดงคำสั่งซื้อทั้งหมด (ไม่ใช่แค่ของตัวเอง)
    all_orders = Order.objects.all().select_related('user', 'pet').order_by('-order_date')
    
    # สถิติสำหรับผู้ขาย (เฉพาะที่เกี่ยวข้องกับสัตว์เลี้ยงของตัวเอง)
    seller_orders = Order.objects.filter(pet__created_by=request.user)
    total_orders = seller_orders.count()
    pending_orders = seller_orders.filter(status='pending').count()
    completed_orders = seller_orders.filter(status='completed').count()
    cancelled_orders = seller_orders.filter(status='cancelled').count()
    
    # ส่ง STATUS_CHOICES ไปยัง template
    status_choices = Order.STATUS_CHOICES
    
    return render(request, 'orders/seller_dashboard.html', {
        'orders': all_orders,  # ส่งคำสั่งซื้อทั้งหมดไปแสดง
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'status_choices': status_choices,  # เพิ่มบรรทัดนี้
    })

@login_required
def update_order_status(request, order_id):
    """อัพเดทสถานะคำสั่งซื้อ (สำหรับ seller)"""
    order = get_object_or_404(Order, id=order_id)
    
    # ตรวจสอบสิทธิ์ - เฉพาะ seller ที่เป็นเจ้าของสัตว์เลี้ยง
    if not request.user.is_seller() or order.pet.created_by != request.user:
        messages.error(request, "คุณไม่มีสิทธิ์อัพเดทคำสั่งซื้อนี้")
        return redirect('seller_dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'อัพเดทสถานะคำสั่งซื้อ #{order.id} เป็น "{order.get_status_display()}" สำเร็จ')
        else:
            messages.error(request, 'สถานะไม่ถูกต้อง')
    
    return redirect('seller_dashboard')