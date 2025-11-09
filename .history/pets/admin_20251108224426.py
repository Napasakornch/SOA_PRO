from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Pet

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    ordering = ('name',)

class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'gender', 'is_available', 'created_by', 'image_preview', 'created_at')
    list_filter = ('category', 'gender', 'is_available', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    list_editable = ('price', 'is_available')
    readonly_fields = ('created_at', 'updated_at', 'image_preview_large')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'price')
        }),
        ('Image Options', {
            'fields': ('image', 'image_url', 'image_preview_large'),
            'description': 'คุณสามารถอัพโหลดรูปภาพหรือใส่ URL ของรูปภาพได้'
        }),
        ('Details', {
            'fields': ('gender', 'is_available')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        """แสดงรูปภาพขนาดเล็กใน list view"""
        if obj.image_display:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />',
                obj.image_display
            )
        return "ไม่มีรูปภาพ"
    image_preview.short_description = 'รูปภาพ'
    
    def image_preview_large(self, obj):
        """แสดงรูปภาพขนาดใหญ่ใน form view"""
        if obj.image_display:
            return format_html(
                '<img src="{}" style="width: 200px; height: 200px; object-fit: cover; border: 1px solid #ddd; border-radius: 4px;" /><br><small>{}</small>',
                obj.image_display,
                obj.image_display
            )
        return "ไม่มีรูปภาพ"
    image_preview_large.short_description = 'Preview รูปภาพ'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # ถ้าเป็นการสร้างใหม่
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    class Media:
        css = {
            'all': ('admin/css/pet_admin.css',)
        }

admin.site.register(Category, CategoryAdmin)
admin.site.register(Pet, PetAdmin)