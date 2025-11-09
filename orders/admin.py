from django.contrib import admin
from .models import Order

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'pet', 'quantity', 'total_price', 'status', 'delivery_method', 'pickup_date', 'recipient_name', 'order_date')
    list_filter = ('status', 'order_date', 'delivery_method')
    search_fields = ('user__username', 'user__email', 'pet__name', 'recipient_name')
    list_editable = ('status',)
    readonly_fields = ('order_date', 'updated_at', 'total_price')
    ordering = ('-order_date',)
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'pet', 'quantity', 'total_price')
        }),
        ('Delivery Information', {
            'fields': ('delivery_method', 'pickup_date', 'recipient_name')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Dates', {
            'fields': ('order_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_price_display(self, obj):
        return f"฿{obj.total_price:,.2f}"
    total_price_display.short_description = 'Total Price'

admin.site.register(Order, OrderAdmin)