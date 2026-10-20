
from django.db.models import Q
from .models import Product, Category, HeroBanner, Review, Wishlist 
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .cart import Cart
from django.db import transaction
from .forms import OrderCreateForm
from .models import OrderItem, Order
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Coupon
from .forms import CouponApplyForm
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from sslcommerz_lib import SSLCOMMERZ
from .forms import ReviewForm
from django.http import HttpResponse, Http404
from .utils import render_to_pdf
from .emails import send_order_confirmation_email, send_low_stock_alert_email

import json
from datetime import timedelta


from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Avg, F
from django.db.models.functions import TruncDate
from django.contrib.auth.models import User




def home_view(request):
    # হিরো স্লাইডার
    banners = HeroBanner.objects.filter(is_active=True)

    # মূল প্রোডাক্ট কুয়েরি
    products = Product.objects.filter(is_available=True).select_related('category')

    # ১. ক্যাটাগরি ফিল্টারিং (URL: ?category=electronics)
    selected_category_slug = request.GET.get('category')
    current_category = None
    if selected_category_slug:
        current_category = get_object_or_404(Category, slug=selected_category_slug)
        products = products.filter(category=current_category)

    # ২. সার্চ কুয়েরি (URL: ?q=phone)
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # ৩. দামের সর্টিং (URL: ?sort=price_low)
    sort = request.GET.get('sort')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    else:
        products = products.order_by('-created_at')

    context = {
        'banners': banners,
        'products': products,
        'selected_category': current_category,
        'search_query': query or '',
        'total_count': products.count(),
    }
    return render(request, 'store/home.html', context)




# ১. কার্টে যোগ করা (POST)
@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    override = request.POST.get('override') == 'True'
    
    cart.add(product=product, quantity=quantity, override_quantity=override)
    return redirect('cart_detail')

# ২. কার্ট থেকে বাদ দেওয়া
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart_detail')

# ৩. কার্ট ড্যাশবোর্ড পেজ
def cart_detail(request):
    cart = Cart(request)
    return render(request, 'store/cart_detail.html', {'cart': cart})




def checkout_view(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('home')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        payment_method = request.POST.get('payment_method', 'COD')

        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                if request.user.is_authenticated:
                    order.user = request.user

                order.total_amount = cart.get_total_price()
                order.payment_method = (
                    'Online Payment (SSLCommerz)'
                    if payment_method == 'SSLCOMMERZ'
                    else 'Cash on Delivery'
                )
                order.save()

                low_stock_products = []

                for item in cart:
                    product = item['product']
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        price=item['price'],
                        quantity=item['quantity'],
                    )
                    product.stock -= item['quantity']
                    product.save()

                    threshold = getattr(settings, 'LOW_STOCK_THRESHOLD', 5)
                    if product.stock <= threshold:
                        low_stock_products.append(product)

                cart.clear()

                send_order_confirmation_email(order)
                for low_prod in low_stock_products:
                    send_low_stock_alert_email(low_prod)

            # redirects placed OUTSIDE the atomic block, after clean commit
            if payment_method == 'SSLCOMMERZ':
                return redirect('initiate_sslcommerz_payment', order_id=order.id)
            return redirect('order_success', order_id=order.id)

        # invalid form → fall through to the render at the bottom
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
            }
        form = OrderCreateForm(initial=initial_data)

    return render(request, 'store/checkout.html', {'cart': cart, 'form': form})

def order_success_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/order_success.html', {'order': order})




# --- ১. কাস্টমার রেজিস্ট্রেশন ও লগইন ভিউ ---

def customer_register(request):
    if request.user.is_authenticated:
        return redirect('customer_dashboard')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "আপনার অ্যাকাউন্ট সফলভাবে তৈরি হয়েছে!")
            return redirect('customer_dashboard')
    else:
        form = UserCreationForm()
        
    return render(request, 'store/auth_register.html', {'form': form})


def customer_login(request):
    if request.user.is_authenticated:
        return redirect('customer_dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.info(request, f"স্বাগতম, {user.username}!")
            # ইউজার কোনো সুরক্ষিত পেজ থেকে আসলে সেখানে ফেরত পাঠাবে
            next_url = request.GET.get('next', 'customer_dashboard')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
        
    return render(request, 'store/auth_login.html', {'form': form})


def customer_logout(request):
    logout(request)
    messages.info(request, "আপনি সফলভাবে লগআউট হয়েছেন।")
    return redirect('home')


# --- ২. কাস্টমার ড্যাশবোর্ড ও অর্ডার হিস্ট্রি ---

@login_required(login_url='customer_login')
def customer_dashboard(request):
    # শুধুমাত্র বর্তমান লগইন থাকা ইউজারের অর্ডারগুলো নতুন থেকে পুরোনো ক্রমানুসারে আনা
    user_orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    
    # ড্যাশবোর্ড পরিসংখ্যান (Stats)
    total_orders_count = user_orders.count()
    completed_orders_count = user_orders.filter(status='Delivered').count()
    total_spent = user_orders.exclude(status='Cancelled').aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
    
    context = {
        'orders': user_orders,
        'total_orders_count': total_orders_count,
        'completed_orders_count': completed_orders_count,
        'total_spent': total_spent,
    }
    return render(request, 'store/dashboard.html', context)


# --- ৩. অর্ডারের বিস্তারিত ইনভয়েস ভিউ ---

@login_required(login_url='customer_login')
def user_order_detail(request, order_id):
    # নিশ্চিত করা হচ্ছে অর্ডারটি যেন বর্তমান ইউজারেরই হয় (সিকিউরিটি চেক)
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/user_order_detail.html', {'order': order})




@require_POST
def coupon_apply(request):
    now = timezone.now()
    form = CouponApplyForm(request.POST)
    if form.is_valid():
        code = form.cleaned_data['code'].strip().upper()
        try:
            coupon = Coupon.objects.get(
                code__iexact=code,
                valid_from__lte=now,
                valid_to__gte=now,
                is_active=True
            )
            request.session['coupon_id'] = coupon.id
            messages.success(request, f'অভিনন্দন! "{coupon.code}" কুপনটি সফলভাবে প্রয়োগ করা হয়েছে ({coupon.discount}% ছাড়)।')
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None
            messages.error(request, 'দুঃখিত, কুপন কোডটি অবৈধ বা এর মেয়াদ উত্তীর্ণ হয়েছে।')
            
    # যে পেজ থেকে রিকোয়েস্ট এসেছে সেখানে ফেরত পাঠানো
    return redirect(request.META.get('HTTP_REFERER', 'cart_detail'))


def coupon_remove(request):
    if 'coupon_id' in request.session:
        del request.session['coupon_id']
        request.session.modified = True
        messages.info(request, 'কুপনটি সফলভাবে অপসারণ করা হয়েছে।')
    return redirect(request.META.get('HTTP_REFERER', 'cart_detail'))


def cart_detail(request):
    cart = Cart(request)
    coupon_apply_form = CouponApplyForm()
    return render(request, 'store/cart_detail.html', {'cart': cart, 'coupon_apply_form': coupon_apply_form})





# --- ১. SSLCommerz সেশন ইনিশিয়ালাইজার ---

def initiate_sslcommerz_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    sslcz_settings = settings.SSLCOMMERZ_SETTINGS
    sslcz = SSLCOMMERZ(sslcz_settings)
    
    # বর্তমান ডোমেইনের পূর্ণাঙ্গ URL তৈরি করা
    current_domain = request.build_absolute_uri('/')[:-1]
    
    post_body = {
        'total_amount': float(order.total_amount),
        'currency': "BDT",
        'tran_id': f"TXN-{order.id}-{order.created_at.strftime('%Y%m%d%H%M%S')}",
        'success_url': f"{current_domain}/payment/success/",
        'fail_url': f"{current_domain}/payment/fail/",
        'cancel_url': f"{current_domain}/payment/cancel/",
        'emi_option': 0,
        
        # কাস্টমার তথ্য
        'cus_name': f"{order.first_name} {order.last_name}",
        'cus_email': order.email,
        'cus_phone': order.phone,
        'cus_add1': order.address,
        'cus_city': order.city,
        'cus_country': "Bangladesh",
        
        # শিপিং তথ্য
        'shipping_method': "NO",
        'num_of_item': order.items.count(),
        'product_name': "Order Goods",
        'product_category': "General",
        'product_profile': "general"
    }
    
    response = sslcz.createSession(post_body)
    
    if response.get('status') == 'SUCCESS':
        # অর্ডার অবজেক্টে জেনারেট হওয়া ইউনিক ট্রানজ্যাকশন আইডি সংরক্ষণ
        order.transaction_id = post_body['tran_id']
        order.save()
        # সরাসরি পেমেন্ট গেটওয়েতে রিডাইরেক্ট
        return redirect(response['GatewayPageURL'])
    else:
        messages.error(request, "পেমেন্ট গেটওয়েতে সংযোগ করতে সমস্যা হচ্ছে। পুনরায় চেষ্টা করুন।")
        return redirect('checkout')


# --- ২. পেমেন্ট সাকসেস কলব্যাক (Webhook) ---

@csrf_exempt
def payment_success(request):
    if request.method == 'POST':
        payment_data = request.POST
        tran_id = payment_data.get('tran_id')
        val_id = payment_data.get('val_id')
        
        sslcz = SSLCOMMERZ(settings.SSLCOMMERZ_SETTINGS)
        # SSLCommerz সার্ভার থেকে পেমেন্ট সত্যতা যাচাই
        validation_response = sslcz.validationTransactionQuery(val_id)
        
        if validation_response.get('status') == 'VALID' or validation_response.get('status') == 'VALIDATED':
            try:
                order = Order.objects.get(transaction_id=tran_id)
                order.is_paid = True
                order.status = 'Processing'  # পেমেন্ট পাওয়ায় প্রসেসিং স্ট্যাটাস
                order.save()
                
                messages.success(request, "আপনার পেমেন্ট সফলভাবে সম্পন্ন হয়েছে!")
                return redirect('order_success', order_id=order.id)
            except Order.DoesNotExist:
                pass
                
    messages.error(request, "পেমেন্ট ভেরিফিকেশন ব্যর্থ হয়েছে।")
    return redirect('home')


# --- ৩. পেমেন্ট ফেইল্ড ও ক্যানসেল কলব্যাক ---

@csrf_exempt
def payment_fail(request):
    messages.error(request, "আপনার পেমেন্টটি ব্যর্থ হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।")
    return redirect('checkout')

@csrf_exempt
def payment_cancel(request):
    messages.warning(request, "আপনি পেমেন্ট প্রক্রিয়াটি বাতিল করেছেন।")
    return redirect('checkout')




# ১. প্রোডাক্টের বিস্তারিত পেজ
def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    reviews = product.reviews.filter(is_approved=True).select_related('user')
    review_form = ReviewForm()

    # ব্যবহারকারী এই প্রোডাক্টটি ইতিপূর্বে ডেলিভারি পেয়েছেন কি না (Verified Buyer Check)
    user_has_purchased = False
    user_review = None

    if request.user.is_authenticated:
        user_has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            order__status='Delivered',
            product=product
        ).exists()
        user_review = Review.objects.filter(product=product, user=request.user).first()

    context = {
        'product': product,
        'reviews': reviews,
        'review_form': review_form,
        'user_has_purchased': user_has_purchased,
        'user_review': user_review,
    }
    return render(request, 'store/product_detail.html', context)


# ২. রিভিউ সাবমিট বা আপডেট ভিউ
@login_required(login_url='customer_login')
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        # পূর্বের কোনো রিভিউ থাকলে তা আপডেট হবে, না থাকলে নতুন তৈরি হবে
        try:
            review = Review.objects.get(product=product, user=request.user)
            form = ReviewForm(request.POST, instance=review)
            action_text = "আপডেট"
        except Review.DoesNotExist:
            form = ReviewForm(request.POST)
            action_text = "যোগ"

        if form.is_valid():
            new_review = form.save(commit=False)
            new_review.product = product
            new_review.user = request.user
            new_review.save()
            messages.success(request, f"আপনার রিভিউ সফলভাবে {action_text} করা হয়েছে!")
        else:
            messages.error(request, "রিভিউ জমা দিতে সমস্যা হয়েছে। সঠিক মান প্রদান করুন।")

    return redirect('product_detail', slug=product.slug)






# ১. উইশলিস্ট তালিকা পেজ
@login_required(login_url='customer_login')
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product__category')
    return render(request, 'store/wishlist.html', {'wishlist_items': wishlist_items})


# ২. উইশলিস্টে পণ্য টগল করা (না থাকলে যোগ, থাকলে রিমুভ)
@login_required(login_url='customer_login')
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()

    if wishlist_item:
        wishlist_item.delete()
        messages.info(request, f'"{product.name}" আপনার প্রিয় তালিকা থেকে সরানো হয়েছে।')
    else:
        Wishlist.objects.create(user=request.user, product=product)
        messages.success(request, f'"{product.name}" আপনার প্রিয় তালিকায় যুক্ত করা হয়েছে!')

    # আগের পেজে ফেরত পাঠানো
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ৩. উইশলিস্ট থেকে সরাসরি কার্টে স্থানান্তর করা
@login_required(login_url='customer_login')
def wishlist_move_to_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    if product.stock > 0:
        cart.add(product=product, quantity=1)
        # উইশলিস্ট থেকে মুছে ফেলা
        Wishlist.objects.filter(user=request.user, product=product).delete()
        messages.success(request, f'"{product.name}" কার্টে যোগ করা হয়েছে এবং উইশলিস্ট থেকে সরানো হয়েছে।')
    else:
        messages.error(request, 'দুঃখিত, এই পণ্যটির স্টক বর্তমানে শেষ।')

    return redirect('wishlist')





@login_required(login_url='customer_login')
def download_invoice_pdf(request, order_id):
    # সিকিউরিটি চেক: শুধুমাত্র অর্ডারের মালিক অথবা অ্যাডমিন স্টাফ এই PDF ডাউনলোড করতে পারবেন
    if request.user.is_staff:
        order = get_object_or_404(Order, id=order_id)
    else:
        order = get_object_or_404(Order, id=order_id, user=request.user)

    context = {
        'order': order,
        'company_name': 'NovaMart Limited',
        'company_address': 'বাড়ি ১২, রোড ৫, ধানমন্ডি, ঢাকা - ১২০৫',
        'company_phone': '+880 1700-000000',
        'company_email': 'support@novamart.com',
    }

    pdf = render_to_pdf('store/pdf/invoice_pdf.html', context)
    
    if pdf:
        # ব্রাউজারে সরাসরি ডাউনলোড পপ-আপ করানোর জন্য হেডার সেট
        filename = f"Invoice_NovaMart_ORD_{order.id}.pdf"
        content = f"attachment; filename='{filename}'"
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = content
        return response
    
    messages.error(request, "ইনভয়েস PDF জেনারেট করতে সমস্যা হয়েছে।")
    return redirect('user_order_detail', order_id=order.id)





# def checkout_view(request):
#     cart = Cart(request)
#     if len(cart) == 0:
#         return redirect('home')

#     if request.method == 'POST':
#         form = OrderCreateForm(request.POST)
#         payment_method = request.POST.get('payment_method', 'COD')

#         if form.is_valid():
#             with transaction.atomic():
#                 order = form.save(commit=False)
#                 if request.user.is_authenticated:
#                     order.user = request.user
                    
#                 order.total_amount = cart.get_total_price()
#                 order.payment_method = 'Online Payment (SSLCommerz)' if payment_method == 'SSLCOMMERZ' else 'Cash on Delivery'
#                 order.save()

#                 low_stock_products = []

#                 # আইটেম তৈরি এবং স্টক নিরীক্ষণ
#                 for item in cart:
#                     product = item['product']
#                     OrderItem.objects.create(
#                         order=order,
#                         product=product,
#                         price=item['price'],
#                         quantity=item['quantity']
#                     )
                    
#                     # স্টক কমানো
#                     product.stock -= item['quantity']
#                     product.save()

#                     # কম স্টক নিরীক্ষণ (Threshold Check)
#                     threshold = getattr(settings, 'LOW_STOCK_THRESHOLD', 5)
#                     if product.stock <= threshold:
#                         low_stock_products.append(product)

#                 cart.clear()

#                 # ১. গ্রাহককে কনফার্মেশন ইমেইল পাঠানো
#                 send_order_confirmation_email(order)

#                 # ২. কম স্টক থাকা পণ্যগুলোর জন্য অ্যাডমিনকে সতর্কতা ইমেইল পাঠানো
#                 for low_prod in low_stock_products:
#                     send_low_stock_alert_email(low_prod)

#                 # পেমেন্ট মেথড অনুযায়ী রিডাইরেক্ট
#                 if payment_method == 'SSLCOMMERZ':
#                     return redirect('initiate_sslcommerz_payment', order_id=order.id)
                
#                 return redirect('order_success', order_id=order.id)
#     else:
#         # ... ফর্ম ইনিশিয়ালাইজেশন পূর্বের ন্যায় ...
#         pass




@staff_member_required(login_url='customer_login')
def admin_analytics_dashboard(request):
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)

    # --- ১. মূল মেট্রিক্স / KPIs ---
    valid_orders = Order.objects.exclude(status='Cancelled')
    
    total_revenue = valid_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
    total_orders_count = valid_orders.count()
    average_order_value = valid_orders.aggregate(Avg('total_amount'))['total_amount__avg'] or 0.00
    total_customers_count = User.objects.filter(is_staff=False).count()

    # --- ২. শেষ ৭ দিনের দৈনিক বিক্রয় ও রেভিনিউ চার্ট ডেটা (Chart.js এর জন্য) ---
    daily_sales_queryset = (
        valid_orders.filter(created_at__gte=last_7_days)
        .annotate(order_date=TruncDate('created_at'))
        .values('order_date')
        .annotate(
            daily_revenue=Sum('total_amount'),
            daily_orders=Count('id')
        )
        .order_by('order_date')
    )

    chart_dates = []
    chart_revenues = []
    chart_orders = []

    for entry in daily_sales_queryset:
        chart_dates.append(entry['order_date'].strftime('%d %b'))
        chart_revenues.append(float(entry['daily_revenue']))
        chart_orders.append(entry['daily_orders'])

    # --- ৩. ক্যাটাগরিভিত্তিক সেলস শেয়ার (Pie Chart) ---
    category_sales_queryset = (
        OrderItem.objects.filter(order__in=valid_orders)
        .values('product__category__name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:5]
    )

    category_labels = [item['product__category__name'] or 'Unknown' for item in category_sales_queryset]
    category_counts = [item['total_sold'] for item in category_sales_queryset]

    # --- ৪. টপ ৫ বেস্ট সেলিং প্রোডাক্ট ---
    top_products = (
        OrderItem.objects.filter(order__in=valid_orders)
        .values('product__id', 'product__name', 'product__price')
        .annotate(
            units_sold=Sum('quantity'),
            total_sales_generated=Sum(F('quantity') * F('price'))
        )
        .order_by('-units_sold')[:5]
    )

    # --- ৫. সাম্প্রতিক ৫টি অর্ডার ---
    recent_orders = Order.objects.all().order_by('-created_at')[:5]

    context = {
        'total_revenue': total_revenue,
        'total_orders_count': total_orders_count,
        'average_order_value': round(average_order_value, 2),
        'total_customers_count': total_customers_count,
        # JSON ফরম্যাটে চার্টের ডেটা টেমপ্লেটে পাঠানো
        'chart_dates_json': json.dumps(chart_dates),
        'chart_revenues_json': json.dumps(chart_revenues),
        'chart_orders_json': json.dumps(chart_orders),
        'category_labels_json': json.dumps(category_labels),
        'category_counts_json': json.dumps(category_counts),
        'top_products': top_products,
        'recent_orders': recent_orders,
    }
    return render(request, 'store/admin_analytics.html', context)