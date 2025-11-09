from django.db import models
from users.models import CustomUser
from pets.models import Pet

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('pickup', 'รับสินค้าเอง'),
        ('delivery', 'จัดส่งถึงบ้าน'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # ฟิลด์ใหม่สำหรับการรับสินค้าเอง
    delivery_method = models.CharField(
        max_length=20, 
        choices=DELIVERY_METHOD_CHOICES, 
        default='pickup',
        verbose_name="วิธีการรับสินค้า"
    )
    pickup_date = models.DateField(
        blank=True, 
        null=True,
        verbose_name="วันที่มารับสินค้า"
    )
    recipient_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="ชื่อผู้รับสินค้า"
    )
    
    order_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        self.total_price = self.pet.price * self.quantity
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.email}"