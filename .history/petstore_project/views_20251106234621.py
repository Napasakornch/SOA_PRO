# petstore_project/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
from pets.models import Pet, Category
from orders.models import Order

@login_required
def cart(request):
    """หน้าตะกร้าสินค้า"""
    # ดึงข้อมูลจาก localStorage ผ่าน request (จะส่งมาจาก frontend)
    cart_data = request.GET.get('cart', '[]')
    
    try:
        cart_items = json.loads(cart_data)
    except:
        cart_items = []
    
    # ดึงข้อมูลสัตว์เลี้ยงจาก cart
    pets_in_cart = []
    total_price = 0
    
    for item in cart_items:
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
            continue
    
    return render(request, 'orders/cart.html', {
        'pets_in_cart': pets_in_cart,
        'total_price': total_price,
        'cart_count': len(pets_in_cart)
    })

@login_required
def create_order_from_cart(request):
    """สร้างคำสั่งซื้อจากตะกร้า"""
    if request.method == 'POST':
        try:
            cart_data = json.loads(request.POST.get('cart', '[]'))
            
            created_orders = []
            for item in cart_data:
                pet = Pet.objects.get(id=item['petId'])
                quantity = item.get('quantity', 1)
                
                # สร้างคำสั่งซื้อ
                order = Order.objects.create(
                    user=request.user,
                    pet=pet,
                    quantity=quantity,
                    total_price=pet.price * quantity,
                    status='pending'
                )
                created_orders.append(order)
            
            messages.success(request, f'สร้างคำสั่งซื้อสำเร็จ {len(created_orders)} รายการ')
            return redirect('order_list')
            
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            return redirect('cart')
    
    return redirect('cart')