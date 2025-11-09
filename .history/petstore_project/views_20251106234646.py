# petstore_project/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
    categories = Category.objects.all()
    return render(request, 'pets/categories.html', {
        'categories': categories
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
    return render(request, 'orders/order_list.html', {
        'orders': orders
    })

@login_required
def order_detail(request, order_id):
    """หน้ารายละเอียดคำสั่งซื้อ"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def cart(request):
    """หน้าตะกร้าสินค้า"""
    return render(request, 'orders/cart.html')