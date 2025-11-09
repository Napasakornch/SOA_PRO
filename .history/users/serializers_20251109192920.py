from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone', 'password', 'password2')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "รหัสผ่านไม่ตรงกัน"})
        
        if CustomUser.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "ชื่อผู้ใช้นี้มีอยู่แล้ว"})
        
        if CustomUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "อีเมลนี้มีอยู่แล้ว"})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(**validated_data)
        
        # ตั้งค่า role เป็น customer โดย default สำหรับการสมัครทั่วไป
        user.role = 'customer'
        user.save()
        
        return user

class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display_name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role', 'role_display', 'is_staff')

class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer สำหรับ admin เพื่อจัดการบทบาทผู้ใช้"""
    role_display = serializers.CharField(source='get_role_display_name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role', 'role_display', 'is_staff', 'is_superuser', 'date_joined')