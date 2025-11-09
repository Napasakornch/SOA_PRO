from django.db import models
from users.models import CustomUser

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Pet(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='pets/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True, verbose_name='Image URL')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    is_available = models.BooleanField(default=True)
    
    # เพิ่มฟิลด์สต็อก
    stock_quantity = models.IntegerField(default=1, verbose_name="จำนวนคงเหลือ")
    min_stock_threshold = models.IntegerField(default=1, verbose_name="จำนวนขั้นต่ำแจ้งเตือน")
    
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def image_display(self):
        """คืนค่า image URL ที่จะใช้แสดงผล"""
        if self.image:
            return self.image.url
        elif self.image_url:
            return self.image_url
        return None
    
    # เพิ่ม properties และ methods สำหรับจัดการสต็อก
    @property
    def is_out_of_stock(self):
        """ตรวจสอบว่าสินค้าหมดสต็อกหรือไม่"""
        return self.stock_quantity <= 0
    
    @property
    def is_low_stock(self):
        """ตรวจสอบว่าสต็อกต่ำกว่าขั้นต่ำหรือไม่"""
        return 0 < self.stock_quantity <= self.min_stock_threshold
    
    @property
    def is_available_for_sale(self):
        """ตรวจสอบว่าสินค้าพร้อมขายหรือไม่"""
        return self.is_available and not self.is_out_of_stock
    
    @property
    def stock_status(self):
        """คืนค่าสถานะสต็อก"""
        if self.is_out_of_stock:
            return 'out_of_stock'
        elif self.is_low_stock:
            return 'low_stock'
        else:
            return 'in_stock'
    
    @property
    def stock_status_display(self):
        """คืนค่าสถานะสต็อกสำหรับแสดงผล"""
        status_map = {
            'out_of_stock': 'สินค้าหมด',
            'low_stock': 'สต็อกต่ำ',
            'in_stock': 'พร้อมขาย'
        }
        return status_map.get(self.stock_status, 'พร้อมขาย')
    
    def reduce_stock(self, quantity=1):
        """ลดจำนวนสต็อกเมื่อมีการสั่งซื้อ"""
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            self.save()
            return True
        return False
    
    def increase_stock(self, quantity=1):
        """เพิ่มจำนวนสต็อก"""
        self.stock_quantity += quantity
        self.save()
        return True
    
    def set_stock(self, quantity):
        """ตั้งค่าจำนวนสต็อก"""
        if quantity >= 0:
            self.stock_quantity = quantity
            self.save()
            return True
        return False
    
    def get_stock_warning(self):
        """คืนค่า warning message ถ้าสต็อกมีปัญหา"""
        if self.is_out_of_stock:
            return "⚠️ สินค้าหมดสต็อก"
        elif self.is_low_stock:
            return f"⚠️ สต็อกต่ำ (เหลือ {self.stock_quantity} ตัว)"
        return None
    
    class Meta:
        ordering = ['-created_at']