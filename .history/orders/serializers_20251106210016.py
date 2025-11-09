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
        read_only_fields = ('user', 'total_price', 'order_date')