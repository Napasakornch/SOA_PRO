from rest_framework import serializers
from .models import Order
from pets.serializers import PetListSerializer
from users.serializers import UserSerializer

class OrderSerializer(serializers.ModelSerializer):
    pet_details = PetListSerializer(source='pet', read_only=True)
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('user', 'total_price', 'order_date', 'updated_at')
    
    def validate_quantity(self, value):
        """Validation สำหรับจำนวน"""
        if value <= 0:
            raise serializers.ValidationError("จำนวนต้องมากกว่า 0")
        return value
    
    def validate(self, data):
        """Validation สำหรับข้อมูลการสั่งซื้อ"""
        pet = data.get('pet')
        quantity = data.get('quantity', 1)
        
        # เพิ่ม validation ตรวจสอบสต็อก
        if pet and quantity:
            if not pet.is_available:
                raise serializers.ValidationError({
                    "pet": "สัตว์เลี้ยงนี้ไม่พร้อมขายในขณะนี้"
                })
            
            if pet.is_out_of_stock:
                raise serializers.ValidationError({
                    "pet": "สินค้าหมดสต็อก"
                })
            
            if pet.stock_quantity < quantity:
                raise serializers.ValidationError({
                    "pet": f"สต็อกไม่พอ! มีเพียง {pet.stock_quantity} ตัว"
                })
        
        # Validation เดิมสำหรับการจัดส่ง
        delivery_method = data.get('delivery_method')
        pickup_date = data.get('pickup_date')
        recipient_name = data.get('recipient_name')
        
        if delivery_method == 'pickup':
            if not pickup_date:
                raise serializers.ValidationError({
                    "pickup_date": "กรุณาเลือกวันที่มารับสินค้า"
                })
            if not recipient_name:
                raise serializers.ValidationError({
                    "recipient_name": "กรุณากรอกชื่อผู้รับสินค้า"
                })
        
        elif delivery_method == 'delivery':
            if not recipient_name:
                raise serializers.ValidationError({
                    "recipient_name": "กรุณากรอกชื่อผู้รับสินค้า"
                })
        
        return data
    
    def create(self, validated_data):
        """Override create method เพื่อคำนวณ total_price"""
        # คำนวณ total_price จาก pet price และ quantity
        pet = validated_data['pet']
        quantity = validated_data['quantity']
        validated_data['total_price'] = pet.price * quantity
        
        return super().create(validated_data)