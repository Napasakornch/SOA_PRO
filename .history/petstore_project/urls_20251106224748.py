from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from . import views

# สร้าง schema_view ที่ด้านบนของไฟล์
schema_view = get_schema_view(
    openapi.Info(
        title="Pet Store API",
        default_version='v1',
        description="API for Pet Store E-commerce",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@petstore.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/pets/', include('pets.urls')),
    path('api/orders/', include('orders.urls')),
    
    # HTML Views
    path('', views.home, name='home'),
    path('pets/', views.pet_list, name='pet_list'),
    path('categories/', views.categories, name='categories'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('orders/', views.order_list, name='order_list'),
    path('cart/', views.cart, name='cart'),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)