from django.db import models  # ← เพิ่ม import นี้
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404
from .models import Pet, Category
from .serializers import PetSerializer, PetListSerializer, CategorySerializer
from users.permissions import IsSellerOrAdminUser

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PetListSerializer
        return PetSerializer
    
    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            # ถ้าไม่ได้ล็อกอิน ให้ใช้ user แรกในระบบ (ควรเป็น admin)
            admin_user = Category.objects.first().created_by if Category.objects.exists() else None
            if admin_user:
                serializer.save(created_by=admin_user)
            else:
                # ถ้ายังไม่มี user ในระบบ
                from django.contrib.auth import get_user_model
                User = get_user_model()
                admin_user = User.objects.filter(is_staff=True).first()
                if admin_user:
                    serializer.save(created_by=admin_user)
                else:
                    # สร้าง user ชั่วคราวถ้ายังไม่มี
                    admin_user = User.objects.create_user(
                        username='temp_admin', 
                        email='temp@example.com',
                        password='temp_password',
                        is_staff=True
                    )
                    serializer.save(created_by=admin_user)
    
    def get_queryset(self):
        """แสดงเฉพาะสัตว์เลี้ยงที่พร้อมขายและมีสต็อกสำหรับลูกค้า"""
        queryset = Pet.objects.filter(is_available=True)
        
        # สำหรับผู้ใช้ทั่วไป (ลูกค้า) แสดงเฉพาะที่มีสต็อก
        if not self.request.user.is_authenticated or not (self.request.user.is_admin() or self.request.user.is_seller()):
            queryset = queryset.filter(stock_quantity__gt=0)
        
        return queryset.select_related('category', 'created_by')
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def toggle_availability(self, request, pk=None):
        """เปิด/ปิดการขายสัตว์เลี้ยง"""
        pet = self.get_object()
        pet.is_available = not pet.is_available
        pet.save()
        return Response({'is_available': pet.is_available})
    
    # เพิ่ม actions สำหรับจัดการสต็อก
    @action(detail=True, methods=['post'], permission_classes=[IsSellerOrAdminUser])
    def update_stock(self, request, pk=None):
        """อัพเดทจำนวนสต็อก"""
        pet = self.get_object()
        
        # ตรวจสอบสิทธิ์ - เฉพาะเจ้าของหรือ admin
        if request.user.is_seller() and pet.created_by != request.user:
            return Response(
                {"error": "คุณไม่มีสิทธิ์จัดการสต็อกสัตว์เลี้ยงนี้"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        stock_quantity = request.data.get('stock_quantity')
        if stock_quantity is None:
            return Response(
                {"error": "กรุณาระบุจำนวนสต็อก"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stock_quantity = int(stock_quantity)
            if stock_quantity < 0:
                return Response(
                    {"error": "จำนวนสต็อกต้องไม่ต่ำกว่า 0"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            pet.stock_quantity = stock_quantity
            pet.save()
            
            return Response({
                'success': True,
                'message': f'อัพเดทสต็อก {pet.name} เป็น {stock_quantity} ตัวสำเร็จ',
                'stock_quantity': pet.stock_quantity,
                'stock_status': pet.stock_status,
                'stock_status_display': pet.stock_status_display
            })
            
        except ValueError:
            return Response(
                {"error": "จำนวนสต็อกต้องเป็นตัวเลข"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsSellerOrAdminUser])
    def increase_stock(self, request, pk=None):
        """เพิ่มจำนวนสต็อก"""
        pet = self.get_object()
        
        # ตรวจสอบสิทธิ์
        if request.user.is_seller() and pet.created_by != request.user:
            return Response(
                {"error": "คุณไม่มีสิทธิ์จัดการสต็อกสัตว์เลี้ยงนี้"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        quantity = request.data.get('quantity', 1)
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {"error": "จำนวนต้องมากกว่า 0"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            pet.increase_stock(quantity)
            
            return Response({
                'success': True,
                'message': f'เพิ่มสต็อก {pet.name} จำนวน {quantity} ตัวสำเร็จ',
                'stock_quantity': pet.stock_quantity,
                'stock_status': pet.stock_status
            })
            
        except ValueError:
            return Response(
                {"error": "จำนวนต้องเป็นตัวเลข"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsSellerOrAdminUser])
    def reduce_stock(self, request, pk=None):
        """ลดจำนวนสต็อก"""
        pet = self.get_object()
        
        # ตรวจสอบสิทธิ์
        if request.user.is_seller() and pet.created_by != request.user:
            return Response(
                {"error": "คุณไม่มีสิทธิ์จัดการสต็อกสัตว์เลี้ยงนี้"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        quantity = request.data.get('quantity', 1)
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {"error": "จำนวนต้องมากกว่า 0"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if pet.stock_quantity < quantity:
                return Response(
                    {"error": f"สต็อกไม่พอ! มีเพียง {pet.stock_quantity} ตัว"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            pet.reduce_stock(quantity)
            
            return Response({
                'success': True,
                'message': f'ลดสต็อก {pet.name} จำนวน {quantity} ตัวสำเร็จ',
                'stock_quantity': pet.stock_quantity,
                'stock_status': pet.stock_status
            })
            
        except ValueError:
            return Response(
                {"error": "จำนวนต้องเป็นตัวเลข"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsSellerOrAdminUser])
    def low_stock(self, request):
        """รายการสัตว์เลี้ยงที่สต็อกต่ำ"""
        low_stock_pets = Pet.objects.filter(
            stock_quantity__lte=models.F('min_stock_threshold'),
            stock_quantity__gt=0,
            is_available=True
        )
        
        serializer = self.get_serializer(low_stock_pets, many=True)
        return Response({
            'count': low_stock_pets.count(),
            'pets': serializer.data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsSellerOrAdminUser])
    def out_of_stock(self, request):
        """รายการสัตว์เลี้ยงที่หมดสต็อก"""
        out_of_stock_pets = Pet.objects.filter(
            stock_quantity=0,
            is_available=True
        )
        
        serializer = self.get_serializer(out_of_stock_pets, many=True)
        return Response({
            'count': out_of_stock_pets.count(),
            'pets': serializer.data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsSellerOrAdminUser])
    def my_pets_stock(self, request):
        """สต็อกสัตว์เลี้ยงของฉัน (สำหรับ seller)"""
        if request.user.is_seller():
            my_pets = Pet.objects.filter(created_by=request.user, is_available=True)
            
            stock_summary = {
                'total_pets': my_pets.count(),
                'in_stock': my_pets.filter(stock_quantity__gt=models.F('min_stock_threshold')).count(),
                'low_stock': my_pets.filter(
                    stock_quantity__lte=models.F('min_stock_threshold'),
                    stock_quantity__gt=0
                ).count(),
                'out_of_stock': my_pets.filter(stock_quantity=0).count(),
                'pets': PetListSerializer(my_pets, many=True).data
            }
            
            return Response(stock_summary)
        else:
            return Response(
                {"error": "เฉพาะผู้ขายเท่านั้นที่สามารถเข้าถึงได้"}, 
                status=status.HTTP_403_FORBIDDEN
            )
    
    # ✅ เพิ่ม endpoints ใหม่สำหรับลูกค้า
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def check_stock(self, request, pk=None):
        """ตรวจสอบจำนวนสต็อก (สำหรับลูกค้า)"""
        pet = self.get_object()
        
        return Response({
            'pet_id': pet.id,
            'pet_name': pet.name,
            'stock_quantity': pet.stock_quantity,
            'is_available': pet.is_available,
            'is_out_of_stock': pet.is_out_of_stock,
            'stock_status': pet.stock_status,
            'stock_status_display': pet.stock_status_display,
            'can_purchase': pet.is_available and pet.stock_quantity > 0
        })
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def stock_status(self, request):
        """ดูสถานะสต็อกสัตว์เลี้ยงทั้งหมด (สำหรับลูกค้า)"""
        pets = Pet.objects.filter(is_available=True)
        
        stock_data = []
        for pet in pets:
            stock_data.append({
                'id': pet.id,
                'name': pet.name,
                'price': float(pet.price),
                'stock_quantity': pet.stock_quantity,
                'is_out_of_stock': pet.is_out_of_stock,
                'stock_status': pet.stock_status_display,
                'image': pet.image_display,
                'category_name': pet.category.name if pet.category else ''
            })
        
        return Response({
            'count': len(stock_data),
            'available_pets': len([p for p in stock_data if not p['is_out_of_stock']]),
            'out_of_stock_pets': len([p for p in stock_data if p['is_out_of_stock']]),
            'pets': stock_data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def available_pets(self, request):
        """สัตว์เลี้ยงที่พร้อมขาย (มีสต็อก)"""
        available_pets = Pet.objects.filter(
            is_available=True,
            stock_quantity__gt=0
        ).select_related('category')
        
        serializer = self.get_serializer(available_pets, many=True)
        return Response({
            'count': available_pets.count(),
            'pets': serializer.data
        })