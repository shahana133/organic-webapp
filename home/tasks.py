from datetime import timedelta
from django.utils import timezone
from .models import FarmerOrder, Notification

def auto_update_delivered_orders():
    now = timezone.now()
    shipped_orders = FarmerOrder.objects.filter(status='Shipped')
    for order in shipped_orders:
        # If 1 day has passed since last update
        if order.updated_at + timedelta(days=1) <= now:
            order.status = 'Delivered'
            order.save()
            
            # Notify farmer
            Notification.objects.create(
                user=order.farmer,
                message=f"Order {order.order_item.product.name} has been auto-marked as Delivered."
            )
