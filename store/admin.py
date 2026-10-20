from django.contrib import admin
from .models import Category, Product, HeroBanner, Order, OrderItem, Coupon, Review, Wishlist
from django.utils.html import format_html
from django.urls import reverse




@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'discount_price', 'stock', 'is_available', 'category')
    list_filter = ('is_available', 'category')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')



class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0

# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['id', 'first_name', 'last_name', 'phone', 'total_amount', 'status', 'created_at']
#     list_filter = ['status', 'created_at']
#     search_fields = ['first_name', 'last_name', 'phone', 'address']
#     list_editable = ['status']  # অ্যাডমিন টেবিল থেকেই সরাসরি স্ট্যাটাস পরিবর্তন করা যাবে
#     inlines = [OrderItemInline]





@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'valid_from', 'valid_to', 'discount', 'is_active']
    list_filter = ['is_active', 'valid_from', 'valid_to']
    search_fields = ['code']




@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['product__name', 'user__username', 'comment']
    list_editable = ['is_approved']



@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']





@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'phone', 'total_amount', 'status', 'is_paid', 'created_at', 'invoice_pdf_link']
    list_filter = ['status', 'is_paid', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone', 'transaction_id']
    list_editable = ['status']

    def invoice_pdf_link(self, obj):
        url = reverse('download_invoice_pdf', args=[obj.id])
        return format_html('<a class="button" style="background-color:#4f46e5; color:white; padding:4px 8px; border-radius:4px; text-decoration:none;" href="{}">PDF ইনভয়েস</a>', url)
    
    invoice_pdf_link.short_description = 'ইনভয়েস'