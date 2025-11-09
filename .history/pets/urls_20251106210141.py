from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PetViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'pets', PetViewSet)
router.register(r'categories', CategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]