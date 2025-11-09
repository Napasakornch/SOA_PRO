from django.db import models
from django.core.exceptions import ValidationError
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
    
    def clean(self):
        """Validation ก่อนบันทึก"""
        # ตรวจสอบสต็อกเมื่อสร้างคำสั่งซื้อใหม่
        if self.pk is None and self.pet and self.quantity:
            if self.pet.is_out_of_stock:
                raise ValidationError(f"ขออภัย {self.pet.name} หมดสต็อกในขณะนี้")
            
            if self.pet.stock_quantity < self.quantity:
                raise ValidationError(
                    f"สต็อก {self.pet.name} ไม่พอ! มีเพียง {self.pet.stock_quantity} ตัว"
                )
    
    def save(self, *args, **kwargs):
        # คำนวณราคารวม
        self.total_price = self.pet.price * self.quantity
        
        # ตรวจสอบ validation
        self.clean()
        
        is_new = self.pk is None
        
        # บันทึกคำสั่งซื้อ
        super().save(*args, **kwargs)
        
        # ลดสต็อกเมื่อสร้างคำสั่งซื้อใหม่
        if is_new:
            self.pet.reduce_stock(self.quantity)
    
    def delete(self, *args, **kwargs):
        """คืนสต็อกเมื่อลบคำสั่งซื้อ"""
        if self.status == 'pending':
            self.pet.increase_stock(self.quantity)
        super().delete(*args, **kwargs)
    
    def cancel_order(self):
        """ยกเลิกคำสั่งซื้อและคืนสต็อก"""
        if self.status == 'pending':
            self.status = 'cancelled'
            self.pet.increase_stock(self.quantity)
            self.save()
            return True
        return False
    
    def complete_order(self):
        """ทำเครื่องหมายว่าสำเร็จ"""
        if self.status == 'pending':
            self.status = 'completed'
            self.save()
            return True
        return False
    
    def update_quantity(self, new_quantity):
        """อัพเดทจำนวนและจัดการสต็อก"""
        if new_quantity <= 0:
            return False, "จำนวนต้องมากกว่า 0"
        
        old_quantity = self.quantity
        
        # ตรวจสอบสต็อกถ้าจำนวนเพิ่มขึ้น
        if new_quantity > old_quantity:
            additional_quantity = new_quantity - old_quantity
            if self.pet.stock_quantity < additional_quantity:
                return False, f"สต็อกไม่พอ! มีเพียง {self.pet.stock_quantity} ตัว"
            
            # ลดสต็อกเพิ่ม
            self.pet.reduce_stock(additional_quantity)
        
        # คืนสต็อกถ้าจำนวนลดลง
        elif new_quantity < old_quantity:
            returned_quantity = old_quantity - new_quantity
            self.pet.increase_stock(returned_quantity)
        
        # อัพเดทจำนวน
        self.quantity = new_quantity
        self.save()
        
        return True, "อัพเดทจำนวนสำเร็จ"
    
    @property
    def can_be_cancelled(self):
        """ตรวจสอบว่าสามารถยกเลิกได้หรือไม่"""
        return self.status == 'pending'
    
    @property
    def can_be_completed(self):
        """ตรวจสอบว่าสามารถทำเครื่องหมายว่าสำเร็จได้หรือไม่"""
        return self.status == 'pending'
    
    @property
    def stock_info(self):
        """ข้อมูลสต็อกสำหรับคำสั่งซื้อนี้"""
        return {
            'pet_name': self.pet.name,
            'current_stock': self.pet.stock_quantity,
            'is_out_of_stock': self.pet.is_out_of_stock,
            'is_low_stock': self.pet.is_low_stock,
            'stock_status': self.pet.stock_status_display
        }
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.email} - {self.pet.name}"
    
    class Meta:
        ordering = ['-order_date']
        verbose_name = 'คำสั่งซื้อ'
        verbose_name_plural = 'คำสั่งซื้อ'