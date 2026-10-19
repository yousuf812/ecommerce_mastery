
from .cart import Cart
from .models import Category, Wishlist

def categories_processor(request):
    return {
        'all_categories': Category.objects.all(),
        'cart': Cart(request),  # এখন সব টেমপ্লেটে {{ cart }} এবং {{ cart|length }} পাওয়া যাবে
    }



def categories_processor(request):
    wishlist_count = 0
    wishlist_product_ids = []

    if request.user.is_authenticated:
        # লগইন থাকা ইউজারের উইশলিস্টের সব প্রোডাক্ট আইডি একটি লিস্টে রাখা
        user_wishlist = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        wishlist_count = user_wishlist.count()
        wishlist_product_ids = list(user_wishlist)

    return {
        'all_categories': Category.objects.all(),
        'cart': Cart(request),
        'wishlist_count': wishlist_count,
        'wishlist_product_ids': wishlist_product_ids, # কার্ডে হার্ট লাল বা ফাঁকা দেখাতে
    }