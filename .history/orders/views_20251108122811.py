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
                    
                    # สร้างคำสั่งซื้อ
                    order = Order.objects.create(
                        user=request.user,
                        pet=pet,
                        quantity=quantity,
                        total_price=pet.price * quantity,
                        status='pending',
                        delivery_method=delivery_method,
                        pickup_date=pickup_date if pickup_date else None,
                        recipient_name=recipient_name
                    )
                    created_orders.append(order)
                    
                except Pet.DoesNotExist:
                    messages.warning(request, 'ไม่พบสัตว์เลี้ยงบางรายการในระบบ')
                    continue
            
            if created_orders:
                messages.success(request, f'สร้างคำสั่งซื้อสำเร็จ {len(created_orders)} รายการ')
                # ล้างตะกร้าหลังสั่งซื้อสำเร็จ
                request.session['cart_cleared'] = True
            else:
                messages.warning(request, 'ไม่สามารถสร้างคำสั่งซื้อได้')
                
            return redirect('order_list')
            
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            return redirect('cart')
    
    return redirect('cart')