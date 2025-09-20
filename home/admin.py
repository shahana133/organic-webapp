from django.contrib import admin
from .models import Product, Category,Order,UserProfile,Address,OrderItem

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Order)
admin.site.register(UserProfile)
admin.site.register(Address)
admin.site.register(OrderItem)
