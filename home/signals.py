from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OrderItem, FarmerOrder, FarmerPayment, Notification, StockAlert, Product

@receiver(post_save, sender=OrderItem)
def create_farmer_records(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        farmer = product.user  # Farmer who owns the product
        quantity = instance.quantity
        total_amount = instance.price * quantity

        # 1️⃣ Create FarmerOrder
        FarmerOrder.objects.create(
            farmer=farmer,
            order_item=instance,
            status=instance.order.status  # Sync initial status
        )

        # 2️⃣ Create FarmerPayment
        FarmerPayment.objects.create(
            farmer=farmer,
            order_item=instance,
            amount=total_amount,
            status='Pending'
        )

        # 3️⃣ Create Notification for new order
        Notification.objects.create(
            user=farmer,
            message=f"New order for {product.name} ({quantity} pcs)."
        )

        # 4️⃣ Check stock alert
        if product.stock - quantity <= 5:  # Threshold can be adjusted
            StockAlert.objects.get_or_create(
                product=product,
                user=farmer,
                threshold=5,
                defaults={'is_alerted': False}
            )

        # Optionally reduce product stock automatically
        product.stock -= quantity
        product.save()

@receiver(post_save, sender=FarmerOrder)
def notify_customer_on_status_change(sender, instance, created, **kwargs):
    if not created:  # Only on updates
        customer = instance.order_item.order.user
        message = f"Your order for {instance.order_item.product.name} is now {instance.status}."
        Notification.objects.create(
            user=customer,
            message=message
        )

@receiver(post_save, sender=OrderItem)
def notify_customer_on_new_order(sender, instance, created, **kwargs):
    if created:
        customer = instance.order.user
        Notification.objects.create(
            user=customer,
            message=f"Your order for {instance.product.name} x {instance.quantity} has been placed successfully!"
        )
