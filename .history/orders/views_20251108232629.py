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
from users.permissions import IsSellerOrAdminUser

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return Order.objects.none()
            
        if user.is_admin() or user.is_seller():
            return Order.objects.all().select_related('user', 'pet')
        else:
            return Order.objects.filter(user=user).select_related('pet')
    
    def perform_create(self, serializer):
        """Auto assign user และ validate ข้อมูล + ตรวจสอบสต็อก"""
        if self.request.user.is_authenticated:
            pet = serializer.validated_data['pet']
            quantity = serializer.validated_data['quantity']
            
            # ตรวจสอบว่าสัตว์เลี้ยงพร้อมขาย
            if not pet.is_available:
                raise serializers.ValidationError({
                    "error": "สัตว์เลี้ยงนี้ไม่พร้อมขายในขณะนี้"
                })
            
            # ตรวจสอบสต็อก
            if pet.is_out_of_stock:
                raise serializers.ValidationError({
                    "error": "สินค้าหมดสต็อก"
                })
            
            if pet.stock_quantity < quantity:
                raise serializers.ValidationError({
                    "error": f"สต็อกไม่พอ! มีเพียง {pet.stock_quantity} ตัว"
                })
            
            # ลดสต็อก
            if not pet.reduce_stock(quantity):
                raise serializers.ValidationError({
                    "error": "ไม่สามารถหักสต็อกได้"
                })
            
            # ตรวจสอบข้อมูลการจัดส่ง
            delivery_method = serializer.validated_data.get('delivery_method', 'pickup')
            recipient_name = serializer.validated_data.get('recipient_name', '')
            
            if not recipient_name:
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
            
        if (request.user.is_admin() or request.user.is_seller()) and 'user_id' in request.GET:
            orders = Order.objects.filter(user_id=request.GET['user_id']).select_related('pet')
        else:
            orders = self.get_queryset()
        
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """ยกเลิกคำสั่งซื้อ + คืนสต็อก"""
        order = self.get_object()
        
        if order.user != request.user and not (request.user.is_admin() or request.user.is_seller()):
            raise PermissionDenied("You can only cancel your own orders.")
        
        if order.status == 'pending':
            # คืนสต็อกเมื่อยกเลิกคำสั่งซื้อ
            order.pet.increase_stock(order.quantity)
            
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
        
        old_status = order.status
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {"error": "Invalid status"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # คืนสต็อกถ้าเปลี่ยนจาก pending เป็น cancelled
        if old_status == 'pending' and new_status == 'cancelled':
            order.pet.increase_stock(order.quantity)
        
        # หักสต็อกถ้าเปลี่ยนจาก cancelled เป็น pending (กรณีย้อนกลับ)
        if old_status == 'cancelled' and new_status == 'pending':
            if order.pet.stock_quantity < order.quantity:
                return Response(
                    {"error": f"สต็อกไม่พอ! มีเพียง {order.pet.stock_quantity} ตัว"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            order.pet.reduce_stock(order.quantity)
        
        order.status = new_status
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def seller_orders(self, request):
        """ดึงคำสั่งซื้อสำหรับ seller (เห็นทั้งหมด)"""
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to view orders.")
        
        if request.user.is_seller() or request.user.is_admin():
            orders = Order.objects.all().select_related('user', 'pet')
            serializer = self.get_serializer(orders, many=True)
            return Response(serializer.data)
        else:
            raise PermissionDenied("Only sellers can access this endpoint.")
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """สถิติคำสั่งซื้อ"""
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to view stats.")
        
        if request.user.is_admin() or request.user.is_seller():
            total_orders = Order.objects.count()
            pending_orders = Order.objects.filter(status='pending').count()
            completed_orders = Order.objects.filter(status='completed').count()
            cancelled_orders = Order.objects.filter(status='cancelled').count()
        else:
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
    
    all_orders = Order.objects.all().select_related('user', 'pet').order_by('-order_date')
    
    # สถิติสำหรับผู้ขาย (เห็นทั้งหมด)
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='completed').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()
    
    # ส่ง STATUS_CHOICES ไปยัง template
    status_choices = Order.STATUS_CHOICES
    
    return render(request, 'orders/seller_dashboard.html', {
        'orders': all_orders,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'status_choices': status_choices,
    })

@login_required
def update_order_status(request, order_id):
    """อัพเดทสถานะคำสั่งซื้อ (สำหรับ seller - จัดการทั้งหมดได้)"""
    order = get_object_or_404(Order, id=order_id)
    
    if not request.user.is_seller():
        messages.error(request, "คุณไม่มีสิทธิ์อัพเดทคำสั่งซื้อนี้")
        return redirect('seller_dashboard')
    
    if request.method == 'POST':
        old_status = order.status
        new_status = request.POST.get('status')
        
        if new_status in dict(Order.STATUS_CHOICES):
            # จัดการสต็อกเมื่อเปลี่ยนสถานะ
            if old_status == 'pending' and new_status == 'cancelled':
                # คืนสต็อกเมื่อยกเลิก
                order.pet.increase_stock(order.quantity)
                messages.info(request, f'คืนสต็อก {order.quantity} ตัวให้ {order.pet.name}')
            
            elif old_status == 'cancelled' and new_status == 'pending':
                # หักสต็อกเมื่อย้อนกลับจากการยกเลิก
                if order.pet.stock_quantity < order.quantity:
                    messages.error(request, 
                        f'สต็อกไม่พอ! {order.pet.name} มีเพียง {order.pet.stock_quantity} ตัว')
                    return redirect('seller_dashboard')
                order.pet.reduce_stock(order.quantity)
                messages.info(request, f'หักสต็อก {order.quantity} ตัวจาก {order.pet.name}')
            
            order.status = new_status
            order.save()
            messages.success(request, f'อัพเดทสถานะคำสั่งซื้อ #{order.id} เป็น "{order.get_status_display()}" สำเร็จ')
        else:
            messages.error(request, 'สถานะไม่ถูกต้อง')
    
    return redirect('seller_dashboard')

@login_required
def update_order(request, order_id):
    """แก้ไขคำสั่งซื้อทั้งหมด (สำหรับ seller - จัดการทั้งหมดได้)"""
    order = get_object_or_404(Order, id=order_id)
    
    if not request.user.is_seller():
        messages.error(request, "คุณไม่มีสิทธิ์แก้ไขคำสั่งซื้อนี้")
        return redirect('seller_dashboard')
    
    if request.method == 'POST':
        try:
            old_quantity = order.quantity
            new_quantity = int(request.POST.get('quantity', order.quantity))
            
            # จัดการสต็อกเมื่อเปลี่ยนจำนวน
            if new_quantity != old_quantity:
                quantity_diff = new_quantity - old_quantity
                
                if quantity_diff > 0:  # ถ้าเพิ่มจำนวน
                    if order.pet.stock_quantity < quantity_diff:
                        messages.error(request, 
                            f'สต็อกไม่พอ! {order.pet.name} มีเพียง {order.pet.stock_quantity} ตัว')
                        return redirect('seller_dashboard')
                    order.pet.reduce_stock(quantity_diff)
                    messages.info(request, f'หักสต็อกเพิ่ม {quantity_diff} ตัวจาก {order.pet.name}')
                
                elif quantity_diff < 0:  # ถ้าลดจำนวน
                    order.pet.increase_stock(abs(quantity_diff))
                    messages.info(request, f'คืนสต็อก {abs(quantity_diff)} ตัวให้ {order.pet.name}')
            
            # อัพเดทข้อมูลอื่นๆ
            order.quantity = new_quantity
            order.status = request.POST.get('status', order.status)
            order.delivery_method = request.POST.get('delivery_method', order.delivery_method)
            order.recipient_name = request.POST.get('recipient_name', order.recipient_name)
            
            pickup_date = request.POST.get('pickup_date')
            order.pickup_date = pickup_date if pickup_date else None
            
            order.save()
            messages.success(request, f'อัพเดทคำสั่งซื้อ #{order.id} สำเร็จ')
            
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
    
    return redirect('seller_dashboard')

@login_required
def update_order_quantity(request, order_id):
    """แก้ไขจำนวนอย่างรวดเร็ว (สำหรับ seller - จัดการทั้งหมดได้) + ตรวจสอบสต็อก"""
    order = get_object_or_404(Order, id=order_id)
    
    if not request.user.is_seller():
        messages.error(request, "คุณไม่มีสิทธิ์แก้ไขคำสั่งซื้อนี้")
        return redirect('seller_dashboard')
    
    if request.method == 'POST':
        try:
            old_quantity = order.quantity
            new_quantity = int(request.POST.get('quantity', 1))
            
            if new_quantity <= 0:
                messages.error(request, 'จำนวนต้องมากกว่า 0')
                return redirect('seller_dashboard')
            
            # จัดการสต็อกเมื่อเปลี่ยนจำนวน
            if new_quantity != old_quantity:
                quantity_diff = new_quantity - old_quantity
                
                if quantity_diff > 0:  # เพิ่มจำนวน
                    if order.pet.stock_quantity < quantity_diff:
                        messages.error(request, 
                            f'สต็อกไม่พอ! {order.pet.name} มีเพียง {order.pet.stock_quantity} ตัว')
                        return redirect('seller_dashboard')
                    order.pet.reduce_stock(quantity_diff)
                
                elif quantity_diff < 0:  # ลดจำนวน
                    order.pet.increase_stock(abs(quantity_diff))
            
            order.quantity = new_quantity
            order.save()
            messages.success(request, f'อัพเดทจำนวนคำสั่งซื้อ #{order.id} เป็น {new_quantity} สำเร็จ')
            
        except ValueError:
            messages.error(request, 'จำนวนไม่ถูกต้อง')
    
    return redirect('seller_dashboard')