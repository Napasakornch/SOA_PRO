from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PetViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'pets', PetViewSet, basename='pet')  # เพิ่ม basename
router.register(r'categories', CategoryViewSet, basename='category')  # เพิ่ม basename

urlpatterns = [
    path('', include(router.urls)),
]