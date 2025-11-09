from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser, AllowAny
from .models import Pet, Category
from .serializers import PetSerializer, PetListSerializer, CategorySerializer

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
        return Pet.objects.filter(is_available=True)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def toggle_availability(self, request, pk=None):
        pet = self.get_object()
        pet.is_available = not pet.is_available
        pet.save()
        return Response({'is_available': pet.is_available})