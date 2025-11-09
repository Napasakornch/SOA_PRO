from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_staff', 'is_active', 'is_superuser')
    list_filter = ('role', 'is_staff', 'is_active', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'phone', 'role'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Override save method ใน admin เพื่อจัดการบทบาทอัตโนมัติ"""
        # ถ้าเป็น superuser ให้ตั้ง role เป็น admin โดยอัตโนมัติ
        if obj.is_superuser and obj.role != 'admin':
            obj.role = 'admin'
        super().save_model(request, obj, form, change)

admin.site.register(CustomUser, CustomUserAdmin)