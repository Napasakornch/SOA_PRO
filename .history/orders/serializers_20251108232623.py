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
    
    def validate(self, data):
        """Validation สำหรับข้อมูลการสั่งซื้อ"""
        delivery_method = data.get('delivery_method')
        pickup_date = data.get('pickup_date')
        recipient_name = data.get('recipient_name')
        
        # Validation สำหรับการรับสินค้าเอง
        if delivery_method == 'pickup':
            if not pickup_date:
                raise serializers.ValidationError({
                    "pickup_date": "กรุณาเลือกวันที่มารับสินค้า"
                })
            if not recipient_name:
                raise serializers.ValidationError({
                    "recipient_name": "กรุณากรอกชื่อผู้รับสินค้า"
                })
        
        # Validation สำหรับการจัดส่ง
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