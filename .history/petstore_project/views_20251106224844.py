from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from pets.models import Pet
from orders.models import Order

def home(request):
    return render(request, 'home.html')

def pet_list(request):
    return render(request, 'pets/pet_list.html')

def pet_detail(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    return render(request, 'pets/pet_detail.html', {'pet': pet})

def categories(request):
    return render(request, 'pets/categories.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'เข้าสู่ระบบสำเร็จ!')
            return redirect('home')
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    
    return render(request, 'auth/login.html')

def register_view(request):
    if request.method == 'POST':
        # ควรเพิ่ม validation ที่นี่
        messages.success(request, 'สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ')
        return redirect('login')
    
    return render(request, 'auth/register.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'ออกจากระบบสำเร็จ')
    return redirect('home')

@login_required
def profile(request):
    return render(request, 'auth/profile.html')

@login_required
def order_list(request):
    return render(request, 'orders/order_list.html')

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def cart(request):
    return render(request, 'orders/cart.html')