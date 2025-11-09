from django.contrib import admin
from .models import Category, Pet

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    ordering = ('name',)

class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'gender', 'is_available', 'created_by', 'created_at')
    list_filter = ('category', 'gender', 'is_available', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    list_editable = ('price', 'is_available')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'price')
        }),
        ('Details', {
            'fields': ('image', 'gender', 'is_available')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # ถ้าเป็นการสร้างใหม่
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Category, CategoryAdmin)
admin.site.register(Pet, PetAdmin)