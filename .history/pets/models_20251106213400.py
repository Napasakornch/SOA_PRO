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
    image_url = models.URLField(blank=True, null=True, verbose_name='Image URL')  # เพิ่มฟิลด์นี้
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    is_available = models.BooleanField(default=True)
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