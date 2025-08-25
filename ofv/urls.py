"""
URL configuration for ofv project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from home.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',homefn),
    path('category/<int:cid>/', categoryproductsfn),
    path('allcategories/', allcategoriesfn),
    path('login/',loginfn),
    path('logout/',logoutfn),
    path('deleteaccount/', deleteaccountfn),
    path('addproduct/',addproductfn),
    path('products/',productsfn),
    path('viewproduct/<int:product_id>/',viewproductfn),
    path('addreview/<int:product_id>/',addreviewfn),
    path('myproducts/',myproductsfn),
    path('editproduct/<int:pid>/',editproductfn),
    path('deleteproduct/<int:pid>/',deleteproductfn),
    
    path('addtocart/<int:pid>/',addtocartfn),
    path('viewcart/', viewcartfn),
    path('removefromcart/<int:pid>/', removefromcartfn),

    path('checkout/', checkoutfn),
    path('placeorder/', placeorderfn),
    path('upi-payment/', upi_payment),
    path('card-payment/', card_payment),
    path('netbanking-payment/', netbanking_payment),
    path('ordersuccess/<int:order_id>/', ordersuccessfn),
    path('myorders/', myordersfn),

    path('register/', registerfn),
    path('farmerprofile/', farmerprofilefn),
    path('customerprofile/', customerprofilefn),

    path('changepassword/', changepasswordfn),
    path('changepassworddone/', changepassworddonefn),
    
    path('updatecartqty/<int:pid>/', updatecartqtyfn),
    path('addaddress/', addaddressfn),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')

