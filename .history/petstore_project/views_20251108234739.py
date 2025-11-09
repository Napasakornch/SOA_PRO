# petstore_project/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime
import json
from pets.models import Pet, Category
from orders.models import Order

def home(request):
    """หน้าแรก"""
    # ดึงสัตว์เลี้ยงมาแสดงในหน้าแรก (limit 4 ตัว)
    featured_pets = Pet.objects.filter(is_available=True)[:4]
    categories = Category.objects.all()
    return render(request, 'home.html', {
        'featured_pets': featured_pets,
        'categories': categories
    })

def pet_list(request):
    """หน้ารายการสัตว์เลี้ยงทั้งหมด"""
    # ดึงข้อมูลสัตว์เลี้ยงทั้งหมดที่พร้อมขาย
    pets = Pet.objects.filter(is_available=True)
    
    # กรองตามหมวดหมู่ (ถ้ามี)
    category_id = request.GET.get('category')
    if category_id:
        pets = pets.filter(category_id=category_id)
    
    # ค้นหา (ถ้ามี)
    search_query = request.GET.get('search')
    if search_query:
        pets = pets.filter(name__icontains=search_query)
    
    categories = Category.objects.all()
    
    return render(request, 'pets/pet_list.html', {
        'pets': pets,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query or ''
    })

def pet_detail(request, pet_id):
    """หน้าข้อมูลสัตว์เลี้ยงโดยละเอียด"""
    pet = get_object_or_404(Pet, id=pet_id)
    
    # ดึงสัตว์เลี้ยงที่เกี่ยวข้อง (หมวดหมู่เดียวกัน)
    related_pets = Pet.objects.filter(
        category=pet.category, 
        is_available=True
    ).exclude(id=pet.id)[:4]
    
    return render(request, 'pets/pet_detail.html', {
        'pet': pet,
        'related_pets': related_pets
    })

def categories(request):
    """หน้าหมวดหมู่สัตว์เลี้ยง"""
    categories_list = Category.objects.all().order_by('name')
    
    # คำนวณสถิติ
    total_pets = Pet.objects.filter(is_available=True, stock_quantity__gt=0).count()
    available_pets = Pet.objects.filter(is_available=True, stock_quantity__gt=0).count()
    
    # นับหมวดหมู่ที่มีสัตว์เลี้ยงมากกว่า 0 ตัว
    popular_categories = 0
    for category in categories_list:
        if category.pet_set.filter(is_available=True, stock_quantity__gt=0).count() > 0:
            popular_categories += 1
    
    return render(request, 'pets/categories.html', {
        'categories': categories_list,
        'total_pets': total_pets,
        'available_pets': available_pets,
        'popular_categories': popular_categories,
    })

def login_view(request):
    """หน้าล็อกอิน"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'เข้าสู่ระบบสำเร็จ!')
            
            # ถ้ามี next parameter ให้ redirect ไปที่นั้น
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    
    return render(request, 'auth/login.html')

def register_view(request):
    """หน้าสมัครสมาชิก"""
    if request.method == 'POST':
        # ควรเพิ่ม validation ที่นี่
        messages.success(request, 'สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ')
        return redirect('login')
    
    return render(request, 'auth/register.html')

def logout_view(request):
    """ออกจากระบบ"""
    logout(request)
    messages.success(request, 'ออกจากระบบสำเร็จ')
    return redirect('home')

@login_required
def profile(request):
    """หน้าโปรไฟล์ผู้ใช้"""
    user_orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'auth/profile.html', {
        'user_orders': user_orders
    })

@login_required
def order_list(request):
    """หน้ารายการคำสั่งซื้อ"""
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    
    # คำนวณสถิติ
    total_orders = orders.count()
    pending_orders = orders.filter(status='pending').count()
    completed_orders = orders.filter(status='completed').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    
    return render(request, 'orders/order_list.html', {
        'orders': orders,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders
    })

@login_required
def order_detail(request, order_id):
    """หน้ารายละเอียดคำสั่งซื้อ"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def cart(request):
    """หน้าตะกร้าสินค้า"""
    # ตรวจสอบว่ามีการสร้างคำสั่งซื้อสำเร็จแล้ว
    if request.session.get('order_created'):
        # ล้าง session
        request.session['order_created'] = False
        # ส่ง flag ไปให้ template ล้างตะกร้า
        return render(request, 'orders/cart.html', {
            'pets_in_cart': [],
            'total_price': 0,
            'cart_count': 0,
            'cart_data_json': '[]',
            'clear_cart': True,
            'today': datetime.now().date()
        })
    
    # รับข้อมูล cart จาก query parameters (จะส่งมาจาก frontend)
    cart_data_str = request.GET.get('cart', '[]')
    
    try:
        cart_data = json.loads(cart_data_str)
    except json.JSONDecodeError:
        cart_data = []
    
    # ดึงข้อมูลสัตว์เลี้ยงจาก cart
    pets_in_cart = []
    total_price = 0
    
    for item in cart_data:
        try:
            pet = Pet.objects.get(id=item['petId'])
            quantity = item.get('quantity', 1)
            item_total = pet.price * quantity
            
            pets_in_cart.append({
                'pet': pet,
                'quantity': quantity,
                'total_price': item_total
            })
            
            total_price += item_total
        except Pet.DoesNotExist:
            # ถ้าไม่พบสัตว์เลี้ยง ให้ข้ามไป
            continue
    
    return render(request, 'orders/cart.html', {
        'pets_in_cart': pets_in_cart,
        'total_price': total_price,
        'cart_count': len(pets_in_cart),
        'cart_data_json': json.dumps(cart_data),
        'today': datetime.now().date()
    })

@login_required
def create_order_from_cart(request):
    """สร้างคำสั่งซื้อจากตะกร้า"""
    if request.method == 'POST':
        try:
            cart_data = json.loads(request.POST.get('cart', '[]'))
            delivery_method = request.POST.get('delivery_method', 'pickup')
            pickup_date = request.POST.get('pickup_date')
            recipient_name = request.POST.get('recipient_name', '')
            
            created_orders = []
            for item in cart_data:
                try:
                    pet = Pet.objects.get(id=item['petId'])
                    quantity = item.get('quantity', 1)
                    
                    # ตรวจสอบว่าสัตว์เลี้ยงพร้อมขายหรือไม่
                    if not pet.is_available:
                        messages.warning(request, f'{pet.name} ไม่พร้อมขายในขณะนี้')
                        continue
                    
                    # ตรวจสอบสต็อก
                    if pet.stock_quantity < quantity:
                        messages.warning(request, f'{pet.name} สต็อกไม่พอ! มีเพียง {pet.stock_quantity} ตัว')
                        continue
                    
                    # สร้างคำสั่งซื้อพร้อมข้อมูลการรับสินค้า
                    order = Order.objects.create(
                        user=request.user,
                        pet=pet,
                        quantity=quantity,
                        total_price=pet.price * quantity,
                        status='pending',
                        delivery_method=delivery_method,
                        pickup_date=pickup_date if pickup_date else None,
                        recipient_name=recipient_name or request.user.get_full_name() or request.user.username
                    )
                    created_orders.append(order)
                    
                except Pet.DoesNotExist:
                    messages.warning(request, 'ไม่พบสัตว์เลี้ยงบางรายการในระบบ')
                    continue
            
            if created_orders:
                messages.success(request, f'สร้างคำสั่งซื้อสำเร็จ {len(created_orders)} รายการ')
                # ล้างตะกร้าหลังสั่งซื้อสำเร็จ
                request.session['order_created'] = True
            else:
                messages.warning(request, 'ไม่สามารถสร้างคำสั่งซื้อได้')
                
            return redirect('order_list')
            
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            return redirect('cart')
    
    return redirect('cart')

def get_cart_data(request):
    """API สำหรับดึงข้อมูล cart (ใช้โดย JavaScript)"""
    if request.method == 'GET' and request.user.is_authenticated:
        # ในอนาคตอาจเก็บ cart ไว้ใน database
        return JsonResponse({'cart': []})
    return JsonResponse({'error': 'Unauthorized'}, status=401)

@login_required
def cancel_order(request, order_id):
    """ยกเลิกคำสั่งซื้อ"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        if order.status == 'pending':
            # คืนสต็อกก่อนยกเลิก
            order.pet.increase_stock(order.quantity)
            order.status = 'cancelled'
            order.save()
            messages.success(request, 'ยกเลิกคำสั่งซื้อสำเร็จ และคืนสต็อกแล้ว')
        else:
            messages.error(request, 'ไม่สามารถยกเลิกคำสั่งซื้อนี้ได้')
    
    return redirect('order_detail', order_id=order_id)