from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Count


class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='categoryimages/', null=True, blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Litre'),
        ('ml', 'Millilitre'),
        ('pcs', 'Pieces'),
        ('bottle', 'Bottle'),
        ('packet', 'Packet'),
    ]

    name = models.CharField(max_length=30)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    details = models.TextField()
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    ctgry = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Seller
    created_at = models.DateTimeField(auto_now_add=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')
    stock = models.PositiveIntegerField(default=0)

    def average_rating(self):
        reviews = self.review_set.all()
        if reviews:
            return sum(r.rating for r in reviews) / len(reviews)
        return 0

    def __str__(self):
        return self.name

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address_line = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.full_name}, {self.city}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    review_image = models.ImageField(upload_to='review_photos/', blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} review by {self.user.username}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, default='No address')
    payment_method = models.CharField(max_length=50, default='Cash on Delivery')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}  ({self.status})"

class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.quantity})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[('farmer', 'Farmer'), ('customer', 'Customer'),('admin','admin')])
    phone = models.CharField(max_length=15, blank=True, null=True)
    image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role}) - {self.phone}"

# =========================
# New Models for Farmer Features
# =========================

class FarmerOrder(models.Model):
    """Track orders specific to a farmer's products"""
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farmer_orders')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Farmer {self.farmer.username} - {self.order_item.product.name}"

class FarmerPayment(models.Model):
    """Track payments/earnings for farmers"""
    farmer = models.ForeignKey(User, on_delete=models.CASCADE)
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.farmer.username} - {self.amount} ({self.status})"

class Notification(models.Model):
    """Notifications for farmers/customers"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {'Read' if self.is_read else 'Unread'}"


class StockAlert(models.Model):
    """Low stock alerts for farmers"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    threshold = models.PositiveIntegerField(default=5)
    is_alerted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} - {self.user.username}"
