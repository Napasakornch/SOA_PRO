from rest_framework import serializers
from .models import Pet, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class PetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Pet
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')

class PetListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Pet
        fields = ('id', 'name', 'price', 'image', 'category_name', 'is_available', 'gender')