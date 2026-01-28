from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OrderItem, FarmerOrder, Notification, StockAlert

@receiver(post_save, sender=OrderItem)
def create_farmer_order_and_update_stock(sender, instance, created, **kwargs):
    if created:
        # 1. Create FarmerOrder automatically
        FarmerOrder.objects.create(
            farmer=instance.product.user,
            order_item=instance,
            status='Pending'
        )

        # 2. Reduce product stock
        product = instance.product
        product.stock -= instance.quantity
        if product.stock < 0:
            product.stock = 0
        product.save()

        # 3. Low stock alert
        if product.stock <= 5:
            StockAlert.objects.get_or_create(
                product=product,
                user=product.user,
                defaults={'threshold': 5}
            )

        # 4. Notification to farmer
        Notification.objects.create(
            user=instance.product.user,
            message=f"New order: {instance.product.name} x {instance.quantity}"
        )
