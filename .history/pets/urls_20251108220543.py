from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PetViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'pets', PetViewSet, basename='pet')
router.register(r'categories', CategoryViewSet, basename='category')

# URLs หลักจาก router
urlpatterns = [
    path('', include(router.urls)),
]

# Custom URLs สำหรับ stock management
stock_urlpatterns = [
    # Stock management endpoints
    path('pets/low-stock/', PetViewSet.as_view({'get': 'low_stock'}), name='low-stock'),
    path('pets/out-of-stock/', PetViewSet.as_view({'get': 'out_of_stock'}), name='out-of-stock'),
    path('pets/my-stock/', PetViewSet.as_view({'get': 'my_pets_stock'}), name='my-pets-stock'),
]

urlpatterns += stock_urlpatterns