# ✅ Updated views.py
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Product, Order,Cart,UserProfile,Category,Review,Address,OrderItem
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import ProductForm,UserProfileForm,AddressForm
from django.core.paginator import Paginator
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_POST
from decimal import Decimal

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
    try:
        if request.user.userprofile.role != 'farmer':
            return HttpResponseForbidden("Only farmers can add products.")
    except UserProfile.DoesNotExist:
        return HttpResponseForbidden("User profile not found.")

    if request.method == 'POST':
        name = request.POST['name']
        price = request.POST['price']
        image = request.FILES.get('image')

        if not image:
            messages.error(request, "Image is required.")
            return render(request, 'addproduct.html')

        Product.objects.create(name=name, price=price, image=image, user=request.user)
        messages.success(request, "Product added.")
        return redirect('/myproducts/')
    return render(request, 'addproduct.html')


@login_required
def productsfn(request): 
    all_products = Product.objects.all()
    user_products = []
    categories = Category.objects.all()

    # Filters
    search_query = request.GET.get('q', '')
    selected_category = request.GET.get('category')
    sort_by = request.GET.get('sort')

    # Search
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

    # Show farmer's own products if user is a farmer
    if request.user.is_authenticated and hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'farmer':
        user_products = Product.objects.filter(user=request.user)

    # Paginate
    from django.core.paginator import Paginator
    paginator = Paginator(all_products, 9)
    page = request.GET.get('page')
    paginated_products = paginator.get_page(page)

    return render(request, 'products.html', {
        'products': paginated_products,
        'user_products': user_products,
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

@login_required
def addreviewfn(request, product_id):
    if request.method == 'POST':
        rating = int(request.POST['rating'])
        comment = request.POST['comment']
        product = get_object_or_404(Product, id=product_id)
        Review.objects.create(user=request.user, product=product, rating=rating, comment=comment)
        return redirect(f'/viewproduct/{product_id}/')    

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
    return redirect('/viewcart/')


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

# ------------------ MY ORDERS ------------------
@login_required
def myordersfn(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'myorders.html', {'orders': orders})

@login_required
def orderdetailfn(request, order_id):
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

        # ✅ Address validation
        if not selected_address_id:
            messages.error(request, "Please select a delivery address.")
            return redirect('/checkout/')

        address = get_object_or_404(Address, id=selected_address_id, user=request.user)

        # ✅ Decide whether to use Cart or Buy Now
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

        # 1️⃣ Create the order
        order = Order.objects.create(
            user=request.user,
            address=f"{address.full_name}, {address.address_line}, {address.city}, {address.state}, {address.pincode} | Phone: {address.phone}",
            payment_method=payment_method,
            total_amount=0  # will update later
        )

        # 2️⃣ Add each item
        for pid, qty in source.items():
            product = get_object_or_404(Product, id=pid)
            qty = int(qty)
            line_total = product.price * qty
            subtotal += line_total

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                price=product.price
            )

        # 3️⃣ Delivery charges and total
        delivery = 0 if subtotal == 0 or subtotal >= 500 else 50
        grand_total = subtotal + delivery

        order.total_amount = grand_total
        order.save()

        # ✅ Store order ID for payment
        request.session['latest_order_id'] = order.id

        # 4️⃣ Payment handling + session cleanup
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

@login_required
def farmerprofilefn(request):
    user = request.user
    profile = user.userprofile
    products = Product.objects.filter(user=user)

    if request.method == 'POST':
        # Update User fields
        user.username = request.POST.get('username')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()

        # Update Profile fields
        profile.phone = request.POST.get('phone')
        if 'image' in request.FILES:
            profile.image = request.FILES['image']
        profile.save()

        return redirect('/farmerprofile/')

    return render(request, 'farmerprofile.html', {
        'user': user,
        'profile': profile,
        'products': products,
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
    return render(request, 'customerprofile.html', {'form': form, 'profile': profile, 'orders': orders})


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
# -----------------------------
@login_required
def farmer_dashboardfn(request):
    farmer = request.user
    total_products = Product.objects.filter(user=farmer).count()
    total_orders = FarmerOrder.objects.filter(farmer=farmer).count()
    pending_orders = FarmerOrder.objects.filter(farmer=farmer, status='Pending').count()
    delivered_orders = FarmerOrder.objects.filter(farmer=farmer, status='Delivered').count()
    total_earnings = FarmerPayment.objects.filter(farmer=farmer, status='Completed').aggregate(total=models.Sum('amount'))['total'] or 0
    notifications = Notification.objects.filter(user=farmer, is_read=False).count()

    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'total_earnings': total_earnings,
        'notifications': notifications,
    }
    return render(request, 'farmer/dashboard.html', context)


# -----------------------------
# Farmer Orders
# -----------------------------
@login_required
def farmer_ordersfn(request):
    orders = FarmerOrder.objects.filter(farmer=request.user).order_by('-order_item__order__created_at')
    return render(request, 'farmer/orders.html', {'orders': orders})


# -----------------------------
# Update Farmer Order Status
# -----------------------------
@login_required
def update_farmer_order_statusfn(request, pk):
    order = get_object_or_404(FarmerOrder, pk=pk, farmer=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(FarmerOrder._meta.get_field('status').choices).keys():
            order.status = new_status
            order.save()
            messages.success(request, 'Order status updated successfully.')
        return redirect('farmer_ordersfn')
    return render(request, 'farmer/update_order.html', {'order': order})


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
