from django.urls import path
from .views import (
    home_view, 
    cart_add, 
    cart_remove, 
    cart_detail, 
    checkout_view, 
    order_success_view,
    customer_register,
    customer_login,
    customer_logout,
    customer_dashboard,
    user_order_detail,
    coupon_apply,
    coupon_remove,
    initiate_sslcommerz_payment,
    payment_success,
    payment_fail,
    payment_cancel,
    product_detail_view,
    submit_review,
    wishlist_view,
    toggle_wishlist,
    wishlist_move_to_cart,
    download_invoice_pdf,
    admin_analytics_dashboard,
)

urlpatterns = [
    path('', home_view, name='home'),
    path('cart/', cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', cart_remove, name='cart_remove'),

    # Checkout & Success
    path('checkout/', checkout_view, name='checkout'),
    path('order/success/<int:order_id>/', order_success_view, name='order_success'),

    # Customer Auth & Dashboard
    path('register/', customer_register, name='customer_register'),
    path('login/', customer_login, name='customer_login'),
    path('logout/', customer_logout, name='customer_logout'),
    path('dashboard/', customer_dashboard, name='customer_dashboard'),
    path('dashboard/order/<int:order_id>/', user_order_detail, name='user_order_detail'),

    path('coupon/apply/', coupon_apply, name='coupon_apply'),
    path('coupon/remove/', coupon_remove, name='coupon_remove'),

    path('product/<slug:slug>/', product_detail_view, name='product_detail'),
    path('product/<int:product_id>/review/', submit_review, name='submit_review'),

    path('payment/sslcommerz/<int:order_id>/', initiate_sslcommerz_payment, name='initiate_sslcommerz_payment'),
    path('payment/success/', payment_success, name='payment_success'),
    path('payment/fail/', payment_fail, name='payment_fail'),
    path('payment/cancel/', payment_cancel, name='payment_cancel'),

    path('wishlist/', wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/move-to-cart/<int:product_id>/', wishlist_move_to_cart, name='wishlist_move_to_cart'),

    path('order/<int:order_id>/invoice/pdf/', download_invoice_pdf, name='download_invoice_pdf'),

    path('admin-panel/analytics/', admin_analytics_dashboard, name='admin_analytics_dashboard'),
]