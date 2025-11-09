from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from rest_framework.exceptions import PermissionDenied

@login_required
def seller_dashboard(request):
    """Dashboard สำหรับผู้ขาย"""
    if not request.user.is_seller():
        messages.error(request, "คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
        return redirect('home')
    
    # คำสั่งซื้อที่เกี่ยวข้องกับสัตว์เลี้ยงของผู้ขาย
    seller_orders = Order.objects.filter(
        pet__created_by=request.user
    ).select_related('user', 'pet').order_by('-order_date')
    
    # สถิติสำหรับผู้ขาย
    total_orders = seller_orders.count()
    pending_orders = seller_orders.filter(status='pending').count()
    completed_orders = seller_orders.filter(status='completed').count()
    cancelled_orders = seller_orders.filter(status='cancelled').count()
    
    return render(request, 'orders/seller_dashboard.html', {
        'orders': seller_orders,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
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