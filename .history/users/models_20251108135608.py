from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'ลูกค้า'),
        ('seller', 'ผู้ขาย'),
        ('admin', 'ผู้ดูแลระบบ'),
    ]
    
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='customer',
        verbose_name='บทบาท'
    )
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        """Override save method เพื่อกำหนด role ให้ superuser เป็น admin โดยอัตโนมัติ"""
        if self.is_superuser and self.role != 'admin':
            self.role = 'admin'
        super().save(*args, **kwargs)
    
    def is_seller(self):
        """ตรวจสอบว่าผู้ใช้เป็นผู้ขายหรือไม่"""
        return self.role == 'seller'
    
    def is_admin(self):
        """ตรวจสอบว่าผู้ใช้เป็นผู้ดูแลระบบหรือไม่"""
        return self.role == 'admin' or self.is_superuser or self.is_staff
    
    def is_customer(self):
        """ตรวจสอบว่าผู้ใช้เป็นลูกค้าหรือไม่"""
        return self.role == 'customer'
    
    def get_role_display_name(self):
        """คืนค่าชื่อบทบาทที่แสดงผล"""
        return dict(self.ROLE_CHOICES).get(self.role, 'ลูกค้า')