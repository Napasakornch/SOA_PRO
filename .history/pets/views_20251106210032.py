from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from .models import Pet, Category
from .serializers import PetSerializer, PetListSerializer, CategorySerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'gender', 'is_available']
    search_fields = ['name', 'category__name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PetListSerializer
        return PetSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def toggle_availability(self, request, pk=None):
        pet = self.get_object()
        pet.is_available = not pet.is_available
        pet.save()
        return Response({'is_available': pet.is_available})