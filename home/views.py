# ✅ Updated views.py
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Product, Order,Cart,UserProfile,Category,Review,Address,OrderItem,FarmerOrder,FarmerPayment,Notification,StockAlert
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import ProductForm,UserProfileForm,AddressForm
from django.core.paginator import Paginator
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_POST
from decimal import Decimal
from django.db.models import Sum, Count
from django.views.decorators.cache import never_cache
from django.utils import timezone
from datetime import timedelta
from django.db.models import Prefetch




# Home view

def homefn(request):
    role = None
    if request.user.is_authenticated:
        try:
            role = request.user.userprofile.role
        except:
            pass

    prdcts = Product.objects.all()
    categories = Category.objects.all()
    fresh_products = Product.objects.order_by('-created_at')[:8] 

    return render(request, 'home.html', {
        'prdcts': prdcts,
        'role': role,
        'user': request.user,
        'categories': categories,
        'fresh_products': fresh_products  
    })

@login_required
def allcategoriesfn(request):
    categories = Category.objects.all()
    return render(request, 'allcategories.html', {'categories': categories})

@login_required
def categoryproductsfn(request, cid):
    category = get_object_or_404(Category, id=cid)
    products = Product.objects.filter(ctgry=category)
    return render(request, 'categoryproducts.html', {'category': category, 'products': products})



def registerfn(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        phone = request.POST['phone']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        role = request.POST['role']

        # Required field validation
        if not all([first_name, last_name, username, phone, password, confirm_password, role]):
            messages.error(request, 'All fields are required.')
            return redirect('/register/')

        # Password match
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('/register/')

        # Password length
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return redirect('/register/')

        # Username check
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return redirect('/register/')

        # Phone check
        if UserProfile.objects.filter(phone=phone).exists():
            messages.error(request, 'Phone number already registered.')
            return redirect('/register/')

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        UserProfile.objects.create(user=user, phone=phone, role=role)
        messages.success(request, f'{role.capitalize()} registered successfully. Please login.')
        return redirect('/login/')

    return render(request, 'register.html')


# Login
@never_cache
def loginfn(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        upass = request.POST.get('password')
        user = authenticate(request, username=uname, password=upass)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next', '/products')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')

# Logout
def logoutfn(request):
    logout(request)
    return redirect('/')

# ------------------ PRODUCT ------------------
@login_required
def addproductfn(request):
    # ✅ Only allow farmers
    try:
        if request.user.userprofile.role != 'farmer':
            return HttpResponseForbidden("Only farmers can add products.")
    except UserProfile.DoesNotExist:
        return HttpResponseForbidden("User profile not found.")

    # ✅ Get all categories for the dropdown
    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST['name']
        price = request.POST['price']
        image = request.FILES.get('image')
        category_id = request.POST.get('category')

        # Validate image
        if not image:
            messages.error(request, "Image is required.")
            return render(request, 'addproduct.html', {'categories': categories})

        # Get the selected category or None
        category = Category.objects.get(id=category_id) if category_id else None

        # Create the product
        Product.objects.create(
            name=name,
            price=price,
            image=image,
            ctgry=category,
            user=request.user
        )
        messages.success(request, "✅ Product added successfully!")
        return redirect('/myproducts/')

    # Render the template with categories
    return render(request, 'addproduct.html', {'categories': categories})


@login_required
def productsfn(request): 
    categories = Category.objects.all()
    search_query = request.GET.get('q', '')
    selected_category = request.GET.get('category')
    sort_by = request.GET.get('sort')

    # Start with all products
    all_products = Product.objects.all()

    # ✅ Restrict farmers to only their own products
    if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'farmer':
        all_products = all_products.filter(user=request.user)

    # Search filter
    if search_query:
        all_products = all_products.filter(name__icontains=search_query)

    # Category filter
    if selected_category:
        all_products = all_products.filter(ctgry_id=selected_category)

    # Sort by price
    if sort_by == 'low':
        all_products = all_products.order_by('price')
    elif sort_by == 'high':
        all_products = all_products.order_by('-price')

    # Pagination
    paginator = Paginator(all_products, 9)
    page = request.GET.get('page')
    paginated_products = paginator.get_page(page)

    return render(request, 'products.html', {
        'products': paginated_products,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
        'sort_by': sort_by,
    })


@login_required
def viewproductfn(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.review_set.all()
    return render(request, 'viewproduct.html', {
        'product': product,
        'reviews': reviews
    })
    
# Optional: adjust limits as needed
MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2 MB
ALLOWED_CONTENT_TYPES = ("image/jpeg", "image/png", "image/gif", "image/webp")

@login_required
def addreviewfn(request, order_item_id):
    # Ensure the order item belongs to the logged-in user
    order_item = get_object_or_404(OrderItem, id=order_item_id, order__user=request.user)

    # Only allow review if order is delivered
    if order_item.order.status != 'Delivered':
        return render(request, "review_error.html", {"message": "You can review only after delivery!"})

    # Prevent duplicate review for the same product
    existing_review = Review.objects.filter(product=order_item.product, user=request.user).first()
    if existing_review:
        return render(request, "review_error.html", {"message": "You have already reviewed this product!"})

    # Handle POST (form submission)
    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "").strip()

        # Handle uploaded file
        review_image = request.FILES.get("review_image")

        # Validate image (optional but recommended)
        if review_image:
            content_type = review_image.content_type
            if content_type not in ALLOWED_CONTENT_TYPES:
                messages.error(request, "Unsupported file type. Use JPEG, PNG, GIF or WEBP.")
                return render(request, "add_review.html", {"order_item": order_item})

            if review_image.size > MAX_UPLOAD_SIZE:
                messages.error(request, "Image too large. Max size is 2 MB.")
                return render(request, "add_review.html", {"order_item": order_item})

            # Optional: check dimensions (uncomment if you want to enforce)
            # try:
            #     width, height = get_image_dimensions(review_image)
            #     if width > 4000 or height > 4000:
            #         messages.error(request, "Image dimensions too large.")
            #         return render(request, "add_review.html", {"order_item": order_item})
            # except Exception:
            #     messages.error(request, "Invalid image file.")
            #     return render(request, "add_review.html", {"order_item": order_item})

        # Create review (include image if present)
        review = Review.objects.create(
            product=order_item.product,
            user=request.user,
            rating=rating,
            comment=comment,
            review_image=review_image  # works if Review model has ImageField named review_image
        )

        messages.success(request, "Review submitted successfully.")
        # Redirect to the order detail page
        return redirect(f"/order/{order_item.order.id}/")

    # For GET requests, show the review form
    return render(request, "add_review.html", {"order_item": order_item})


@login_required
def myproductsfn(request):
    user = request.user
    profile = UserProfile.objects.get(user=user)

    if profile.role != 'farmer':
        return render(request, 'unauthorized.html') 

    products = Product.objects.filter(user=user)
    return render(request, 'myproducts.html', {'products': products})

@login_required
def editproductfn(request, pid):
    product = Product.objects.get(id=pid)
    if product.user != request.user:
        return HttpResponseForbidden("You can only edit your own products.")
    
    if request.method == 'POST':
        product.name = request.POST['name']
        product.price = request.POST['price']
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        product.save()
        messages.success(request, "Product updated.")
        return redirect('/myproducts/')
    return render(request, 'editproduct.html', {'product': product})


@login_required
def deleteproductfn(request, pid):
    product = Product.objects.get(id=pid)
    if product.user != request.user:
        return HttpResponseForbidden("You can only delete your own products.")
    product.delete()
    messages.success(request, "Product deleted.")
    return redirect('/myproducts/')

# ------------------ CART ------------------


@login_required
def addtocartfn(request, pid):
    product = get_object_or_404(Product, id=pid)

    # ✅ Prevent farmer from adding their own product
    if product.user == request.user:
        messages.error(request, "You cannot add your own product to the cart.")
        return redirect('/products/')

    # ✅ Add to session cart: { product_id: quantity }
    cart = request.session.get('cart', {})
    cart[str(pid)] = cart.get(str(pid), 0) + 1
    request.session['cart'] = cart

    messages.success(request, f"{product.name} added to your cart!")
    return redirect('/products/')


@login_required
def viewcartfn(request):
    cart = request.session.get('cart', {})
    items = []
    subtotal = 0

    # ✅ Handle quantity update request
    if request.method == 'POST' and 'update_qty' in request.POST:
        pid = request.POST.get('pid')
        new_qty = int(request.POST.get('qty', 1))
        if new_qty <= 0:
            cart.pop(pid, None)  # Remove item if qty <= 0
        else:
            cart[pid] = new_qty
        request.session['cart'] = cart
        return redirect('/viewcart/')  # Refresh page after update

    # ✅ Load cart items
    for pid, qty in cart.items():
        try:
            product = Product.objects.get(id=pid)
            item_total = product.price * qty
            subtotal += item_total
            items.append({'product': product, 'qty': qty, 'subtotal': item_total})
        except Product.DoesNotExist:
            continue

    # ✅ Delivery charges
    if subtotal == 0:
        delivery = 0
    elif subtotal >= 500:
        delivery = 0
    else:
        delivery = 50

    grand_total = subtotal + delivery

    # ✅ Address form
    if request.method == 'POST' and 'address_form' in request.POST:
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "✅ Address added successfully.")
            return redirect('/viewcart/')
        else:
            messages.error(request, "❌ Please correct the errors in address form.")
    else:
        form = AddressForm()

    return render(request, 'viewcart.html', {
        'items': items,
        'subtotal': subtotal,
        'delivery': delivery,
        'grand_total': grand_total,
        'form': form,
        'range': range(1, 11),  # For quantity dropdown
    })


@login_required
def removefromcartfn(request, pid):
    cart = request.session.get('cart', {})
    cart.pop(str(pid), None)
    request.session['cart'] = cart
    return redirect('/viewcart/')

# ------------------ CHECKOUT ------------------
@login_required
def checkoutfn(request):
    """Checkout for Cart or Buy Now session."""
    cart = request.session.get('cart', {})
    buy_now = request.session.get('buy_now')

    # ✅ If cart has items, use it; only use buy_now if cart is empty
    if cart:
        source = cart
        is_buy_now = False
    elif buy_now:
        source = buy_now
        is_buy_now = True
    else:
        messages.error(request, "Your cart is empty. Please add items before checkout.")
        return redirect('/products/')

    items, subtotal = [], 0
    for pid, qty in source.items():
        product = get_object_or_404(Product, id=pid)
        qty = int(qty)
        line_total = product.price * qty
        subtotal += line_total
        items.append({"product": product, "quantity": qty, "total": line_total})

    delivery = 0 if subtotal >= 500 or subtotal == 0 else 50
    grand_total = subtotal + delivery

    context = {
        "items": items,
        "total_price": subtotal,
        "delivery": delivery,
        "total": grand_total,
        "addresses": Address.objects.filter(user=request.user),
        "is_buy_now": is_buy_now,
        "qty_options": list(range(1, 11)),
    }
    return render(request, "checkout.html", context)


@login_required
def myordersfn(request):
    """
    Show all orders for the logged-in customer.
    """
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related('orderitem_set__product')
        .order_by('-created_at')
    )
    return render(request, 'myorders.html', {'orders': orders, 'title': 'My Orders'})

@login_required
def orderhistoryfn(request):
    now = timezone.now()
    all_orders = Order.objects.filter(user=request.user)

    for order in all_orders:
        time_diff = now - order.created_at

        if order.status == 'Pending' and time_diff > timedelta(days=1):
            order.status = 'Shipped'
            order.save()

        elif order.status == 'Shipped' and time_diff > timedelta(days=1, hours=12):
            order.status = 'Out for Delivery'
            order.save()

        elif order.status == 'Out for Delivery' and time_diff > timedelta(days=2):
            order.status = 'Delivered'
            order.save()

            # ✅ Notify customer if not already notified
            if order.user and not Notification.objects.filter(
                user=order.user,
                message__contains=f"order #{order.id} has been delivered"
            ).exists():
                Notification.objects.create(
                    user=order.user,
                    message=f"Your order #{order.id} has been delivered!"
                )

    # Show only completed orders
    past_statuses = ['Delivered', 'Cancelled']
    orders = Order.objects.filter(user=request.user, status__in=past_statuses).prefetch_related(
        Prefetch('orderitem_set', queryset=OrderItem.objects.select_related('product__owner'))
    ).order_by('-created_at')

    return render(request, 'myorders.html', {'orders': orders, 'title': 'Order History'})


@login_required
def orderdetailfn(request, order_id):
    """
    Show order detail only if it belongs to the logged-in customer.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "orderdetail.html", {"order": order})


@login_required
def cancelorderfn(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status == "Pending":  # only allow cancel if not shipped
        order.status = "Cancelled"
        order.save()
        messages.success(request, f"Order #{order.id} has been cancelled.")
    else:
        messages.error(request, f"Order #{order.id} cannot be cancelled (already {order.status}).")

    return redirect('/myorders/')  # 👈 fixed (direct path)

@login_required
def placeorderfn(request):
    if request.method == "POST":
        payment_method = request.POST.get("payment_method")
        selected_address_id = request.POST.get("selected_address")

        # ✅ Validate address
        if not selected_address_id:
            messages.error(request, "Please select a delivery address.")
            return redirect('/checkout/')

        address = get_object_or_404(Address, id=selected_address_id, user=request.user)

        # ✅ Determine source: Cart or Buy Now
        cart = request.session.get('cart', {})
        buy_now = request.session.get('buy_now')

        if cart:
            source = cart
            is_buy_now = False
        elif buy_now:
            source = buy_now
            is_buy_now = True
        else:
            messages.error(request, "Your cart is empty.")
            return redirect('/checkout/')

        subtotal = 0

        # ✅ Prevent farmers from buying their own products
        for pid in source.keys():
            product = get_object_or_404(Product, id=pid)
            if product.user == request.user:
                return redirect(f'/product-restriction/{product.name}/')

        # 1️⃣ Create main Order
        order = Order.objects.create(
            user=request.user,
            address=f"{address.full_name}, {address.address_line}, {address.city}, {address.state}, {address.pincode} | Phone: {address.phone}",
            payment_method=payment_method,
            total_amount=0  # will update after calculating subtotal
        )

        # 2️⃣ Create OrderItem and FarmerOrder for each product
        for pid, qty in source.items():
            product = get_object_or_404(Product, id=pid)
            qty = int(qty)
            line_total = product.price * qty
            subtotal += line_total

            # Create OrderItem
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                price=product.price
            )

            # ✅ Create FarmerOrder linked to the product owner
            FarmerOrder.objects.create(
                farmer=product.user,  # important: product.user is the farmer
                order_item=order_item,
                status='Pending'
            )

            # ✅ Create FarmerPayment record
            FarmerPayment.objects.create(
                farmer=product.user,
                order_item=order_item,
                amount=line_total,
                status='Pending'
            )

        # 3️⃣ Delivery charges and total
        delivery = 0 if subtotal == 0 or subtotal >= 500 else 50
        grand_total = subtotal + delivery
        order.total_amount = grand_total
        order.save()

        # Store latest order ID for payment or confirmation page
        request.session['latest_order_id'] = order.id

        # 4️⃣ Payment handling & cleanup
        if payment_method == "cod":
            if is_buy_now:
                request.session.pop('buy_now', None)
            else:
                request.session.pop('cart', None)
            request.session.modified = True
            messages.success(request, "Order placed successfully with Cash on Delivery!")
            return redirect(f"/ordersuccess/{order.id}/")

        elif payment_method == "upi":
            return redirect('/upi-payment/')
        elif payment_method == "card":
            return redirect('/card-payment/')
        elif payment_method == "netbanking":
            return redirect('/netbanking-payment/')
        else:
            messages.error(request, "Please select a valid payment method.")
            return redirect('/checkout/')

    # If GET request, redirect to home
    return redirect('/')


def product_restrictionfn(request, product_name):
    return render(request, 'product_restriction.html', {'product_name': product_name})



def upi_payment(request):
      return HttpResponse("upi_Payment Page (to be implemented)")



def card_payment(request):
    # fetch order_total from session or database
    order_total = 1000  # example
    return render(request, 'card_payment.html', {'order_total': order_total})


def netbanking_payment(request):
     order_total = 1000  # example
     return render(request, 'netbanking_payment.html', {'order_total': order_total})

@login_required
def ordersuccessfn(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "ordersuccess.html", {"order": order})

@login_required
def buynowfn(request, product_id):
    """Buy Now for single product with farmer restriction."""
    product = get_object_or_404(Product, id=product_id)

    # ✅ Prevent farmer from buying their own product
    if product.user == request.user:
        messages.error(request, "You cannot buy your own product.")
        return redirect(f'/viewproduct/{product_id}/')  # Redirect back to product page

    # ✅ Quantity from GET, default = 1
    try:
        qty = int(request.GET.get("qty", 1))
    except (TypeError, ValueError):
        qty = 1
    qty = max(1, min(10, qty))  # Clamp between 1–10

    # ✅ Save to session for checkout
    request.session['buy_now'] = {str(product_id): qty}
    request.session.modified = True

    subtotal = product.price * qty
    delivery = 0 if subtotal >= 500 or subtotal == 0 else 50
    grand_total = subtotal + delivery

    context = {
        "items": [{"product": product, "quantity": qty, "total": subtotal}],
        "total_price": subtotal,
        "delivery": delivery,
        "total": grand_total,
        "addresses": Address.objects.filter(user=request.user),
        "is_buy_now": True,
        "qty_options": list(range(1, 11)),
    }
    return render(request, "checkout.html", context)

# ------------------ PROFILE ------------------
# ------------------ PROFILE ------------------
@login_required
def farmerprofilefn(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile = user.userprofile
    products = Product.objects.filter(user=user)
    is_owner = request.user == user

    # ✅ Fetch notifications (only for the owner)
    notifications = []
    stock_alerts = []
    if is_owner:
        notifications = Notification.objects.filter(user=user).order_by('-created_at')
        stock_alerts = StockAlert.objects.filter(farmer=user).order_by('-created_at')

    # ✅ Profile update
    if request.method == 'POST' and is_owner:
        user.username = request.POST.get('username')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()

        profile.phone = request.POST.get('phone')
        if 'image' in request.FILES:
            profile.image = request.FILES['image']
        profile.save()
        return redirect(f'/farmerprofile/{user.pk}/')

    return render(request, 'farmerprofile.html', {
        'user': user,
        'profile': profile,
        'products': products,
        'is_owner': is_owner,
        'notifications': notifications,
        'stock_alerts': stock_alerts
    })
@login_required
def customerprofilefn(request):
    profile = UserProfile.objects.get(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            user = request.user
            user.username = request.POST.get('username', user.username)
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.save()
            form.save()
            return redirect('/customerprofile/')
    else:
        form = UserProfileForm(instance=profile)

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'customerprofile.html', {
        'form': form,
        'profile': profile,
        'orders': orders,
        'notifications': notifications
    })

@login_required
def deleteaccountfn(request):
    if request.method == 'POST':
        user = request.user
        logout(request)  # Logout before deletion to avoid session issues
        user.delete()
        messages.success(request, "Your account has been deleted successfully.")
        return redirect('/')
    return HttpResponseForbidden("Invalid request")

@login_required
def changepasswordfn(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)  # Keep user logged in
            messages.success(request, '✅ Password changed successfully.')
            return redirect('/changepassworddone/')
        else:
            messages.error(request, '❌ Please correct the errors below.')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'changepassword.html', {'form': form})



@login_required
def changepassworddonefn(request):
    return render(request, 'changepassworddone.html')    


@login_required
def updatecartqtyfn(request, pid):
    if request.method == "POST":
        qty = int(request.POST.get("qty", 1))
        cart = request.session.get("cart", {})
        if str(pid) in cart:
            cart[str(pid)] = qty
            request.session["cart"] = cart
            messages.success(request, "Quantity updated.")
    return redirect("/viewcart/")


@login_required
def addaddressfn(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address_line = request.POST.get('address_line')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')

        if not (full_name and phone and address_line and city and state and pincode):
            messages.error(request, 'All address fields are required.')
            return redirect('/checkout/')

        Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            address_line=address_line,
            city=city,
            state=state,
            pincode=pincode
        )

        messages.success(request, 'Address added successfully.')
        return redirect('/checkout/')

    return redirect('/checkout/')



# -----------------------------
# Farmer Dashboard
# ----------------------------

@login_required
def farmer_dashboardfn(request):
    farmer = request.user

    # Total products
    total_products = Product.objects.filter(user=farmer).count()

    # Farmer Orders (per farmer, per product)
    farmer_orders_qs = FarmerOrder.objects.filter(farmer=farmer)
    total_orders = farmer_orders_qs.count()
    pending_orders = farmer_orders_qs.filter(status='Pending').count()
    delivered_orders = farmer_orders_qs.filter(status='Delivered').count()

    # Earnings calculation
    total_earnings = farmer_orders_qs.filter(status='Delivered').aggregate(
        total=Sum('order_item__price')
    )['total'] or 0

    # Customers who bought products
    customers = farmer_orders_qs.values_list('order_item__order__user__username', flat=True).distinct()

    # Notifications for farmer
    unread_notifications = Notification.objects.filter(user=farmer, is_read=False).count()
    notifications = Notification.objects.filter(user=farmer).order_by('-created_at')

    # Stock alerts
    stock_alerts = StockAlert.objects.filter(product__user=farmer)
    stock_alert_count = stock_alerts.count()

    return render(request, 'farmer/dashboard.html', {
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'total_earnings': total_earnings,
        'customers': customers,
        'unread_notifications': unread_notifications,
        'notifications': notifications,
        'stock_alert_count': stock_alert_count,
        'stock_alerts': stock_alerts,
    })

# -----------------------------
# Farmer Orders
# -----------------------------
@login_required
def farmer_ordersfn(request):
    if request.method == 'POST':
        order_id = request.POST.get('farmer_order_id')  # hidden input in template
        farmer_order = get_object_or_404(FarmerOrder, id=order_id, farmer=request.user)

        new_status = request.POST.get('status')
        valid_statuses = ['Pending', 'Shipped', 'Delivered', 'Cancelled']

        if new_status in valid_statuses:
            farmer_order.status = new_status
            farmer_order.save()
            messages.success(request, f"Order #{farmer_order.id} status updated to {new_status}.")

            # Update main order status if all farmer orders are delivered
            main_order = farmer_order.order_item.order
            all_farmer_orders = FarmerOrder.objects.filter(order_item__order=main_order)
            if all(f.status == 'Delivered' for f in all_farmer_orders):
                if main_order.status != 'Delivered':  # avoid duplicate updates
                    main_order.status = 'Delivered'
                    main_order.save()

                    # ✅ Notify customer (once only)
                    if main_order.user and not Notification.objects.filter(
                        user=main_order.user,
                        message__contains=f"order #{main_order.id} has been delivered"
                    ).exists():
                        Notification.objects.create(
                            user=main_order.user,
                            message=f"Your order #{main_order.id} has been delivered!"
                        )
        else:
            messages.error(request, "Invalid status selected.")

        return redirect('/farmerorders/')

    # GET request: show only the farmer's orders
    orders = FarmerOrder.objects.filter(farmer=request.user).select_related(
        'order_item', 'order_item__product', 'order_item__order'
    ).order_by('-id')

    return render(request, 'farmer/orders.html', {'orders': orders})
# -----------------------------
# Farmer Payments
# -----------------------------
@login_required
def farmer_paymentsfn(request):
    payments = FarmerPayment.objects.filter(farmer=request.user).order_by('-created_at')
    return render(request, 'farmer/payments.html', {'payments': payments})


# -----------------------------
# Farmer Notifications
# -----------------------------
@login_required
def farmer_notificationsfn(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    # Mark all as read
    notifications.update(is_read=True)
    return render(request, 'farmer/notifications.html', {'notifications': notifications})


# -----------------------------
# Farmer Stock Alerts
# -----------------------------
@login_required
def farmer_stock_alertsfn(request):
    alerts = StockAlert.objects.filter(user=request.user, is_alerted=False)
    return render(request, 'farmer/stock_alerts.html', {'alerts': alerts})


# -----------------------------
# Farmer Products
# -----------------------------
@login_required
def farmer_productsfn(request):
    products = Product.objects.filter(user=request.user)
    return render(request, 'farmer/products.html', {'products': products})

@login_required
def customer_notificationsfn(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'customer_notifications.html', {'notifications': notifications})

# Admin dashboard view
@login_required
def admin_dashboard(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return HttpResponseForbidden("You are not allowed here")

    products = Product.objects.all()
    orders = Order.objects.all()
    farmers = UserProfile.objects.filter(role='farmer')
    customers = UserProfile.objects.filter(role='customer')

    return render(request, 'admin_dashboard.html', {
        'products': products,
        'orders': orders,
        'farmers': farmers,
        'customers': customers,
    })

# Action: Approve a product
@login_required
def approve_product(request, product_id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return HttpResponseForbidden("Not allowed")
    product = get_object_or_404(Product, id=product_id)
    product.approved = True  # assuming you have this field
    product.save()
    return redirect('/admin-dashboard/')

# Action: Update order status
@login_required
def update_order_status(request, order_id, status):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return HttpResponseForbidden("Not allowed")
    order = get_object_or_404(Order, id=order_id)
    order.status = status
    order.save()
    return redirect('/admin-dashboard/')

# Block/unblock user
@login_required
def toggle_user_status(request, user_id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return HttpResponseForbidden("Not allowed")
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active  # toggle active status
    user.save()
    return redirect('/admin-dashboard/')


@login_required
def helpcenterfn(request):
    if request.user.role == "customer":
        return render(request, "customerhelpcenter.html")
    elif request.user.role == "farmer":
        return render(request, "farmerhelpcenter.html")
