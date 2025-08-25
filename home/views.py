# ✅ Updated views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Product, Order,Cart,UserProfile,Category,Review,Address
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
    search_query = request.GET.get('search', '')
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
    cart = request.session.get('cart', {})
    cart[str(pid)] = cart.get(str(pid), 0) + 1
    request.session['cart'] = cart
    return redirect('/viewcart/')

@login_required
def viewcartfn(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0

    for pid, qty in cart.items():
        try:
            product = Product.objects.get(id=pid)
            subtotal = product.price * qty
            total += subtotal
            items.append({'product': product, 'qty': qty, 'subtotal': subtotal})
        except Product.DoesNotExist:
            continue

    # Handle address form
    if request.method == 'POST':
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
        'total': total,
        'form': form,
        'range': range(1, 11),
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
    cart = request.session.get('cart', {})
    items = []
    total = 0

    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        item_total = product.price * quantity
        total += item_total
        items.append({'product': product, 'quantity': quantity, 'total': item_total})

    addresses = Address.objects.filter(user=request.user)

    context = {
        'items': items,
        'total_price': total,
        'addresses': addresses,
    }
    return render(request, 'checkout.html', context)


# ------------------ MY ORDERS ------------------
@login_required
def myordersfn(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'myorders.html', {'orders': orders})

@login_required
def placeorderfn(request):
    if request.method == "POST":
        payment_method = request.POST.get("payment_method")
        selected_address_id = request.POST.get("selected_address")

        if not selected_address_id:
            messages.error(request, "Please select a delivery address.")
            return redirect('/checkout/')

        # fetch selected address
        address = get_object_or_404(Address, id=selected_address_id, user=request.user)

        # fetch cart from session (not DB)
        cart = request.session.get('cart', {})
        if not cart:
            messages.error(request, "Your cart is empty.")
            return redirect('/checkout/')

        items = []
        total = 0
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=product_id)
            item_total = product.price * quantity
            total += item_total
            items.append({'product': product, 'quantity': quantity, 'total': item_total})

        # create order
        order = Order.objects.create(
            user=request.user,
            address=f"{address.full_name}, {address.address_line}, {address.city}, {address.state}, {address.pincode} | Phone: {address.phone}",
            payment_method=payment_method,
            total_amount=total
        )

        # clear session cart
        request.session['cart'] = {}

        # handle payment method
        if payment_method == "cod":
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



def upi_payment(request):
    return HttpResponse("UPI Payment Page (to be implemented)")

def card_payment(request):
    return HttpResponse("Card Payment Page (to be implemented)")

def netbanking_payment(request):
    return HttpResponse("Net Banking Payment Page (to be implemented)")

@login_required
def ordersuccessfn(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "ordersuccess.html", {"order": order})



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


