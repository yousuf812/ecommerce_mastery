from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import Avg



class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome বা SVG আইকন নাম (উদা: shirt, laptop)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=10)
    image = models.ImageField(upload_to='products/%Y/%m/')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def get_average_rating(self):
        """প্রোডাক্টের গড় স্টার রেটিং (যেমন: ৪.৫) হিসাব করে"""
        avg = self.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0

    def get_review_count(self):
        """অনুমোদিত মোট রিভিউ সংখ্যা গণনা করে"""
        return self.reviews.filter(is_approved=True).count()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class HeroBanner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='banners/')
    link_url = models.CharField(max_length=255, default='#')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title




# ... পূর্ববর্তী Category, Product, HeroBanner মডেল অপরিবর্তিত থাকবে ...

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'অপেক্ষমান (Pending)'),
        ('Processing', 'প্রক্রিয়াধীন (Processing)'),
        ('Shipped', 'ডেলিভারিতে আছে (Shipped)'),
        ('Delivered', 'সম্পন্ন (Delivered)'),
        ('Cancelled', 'বাতিল (Cancelled)'),
    )

    # ইউজার লগইন না থাকলেও যেন গেস্ট হিসেবে অর্ডার করতে পারে (null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=50, default='Cash on Delivery')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"অর্ডার #{self.id} - {self.first_name} {self.last_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

    def get_cost(self):
        return self.price * self.quantity




class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, help_text="কুপন কোড (যেমন: SAVE20)")
    valid_from = models.DateTimeField(help_text="কুপন শুরুর তারিখ ও সময়")
    valid_to = models.DateTimeField(help_text="কুপনের মেয়াদ শেষের তারিখ ও সময়")
    discount = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="ডিসকাউন্ট শতাংশ (১ থেকে ১০০%)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_to

    def __str__(self):
        return f"{self.code} ({self.discount}% ছাড়)"



# --- নতুন Review মডেল ---
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="১ থেকে ৫ স্টার রেটিং"
    )
    comment = models.TextField(help_text="পণ্যের গুণগত মান নিয়ে বিস্তারিত মতামত")
    is_approved = models.BooleanField(default=True, help_text="স্প্যাম রোধে মডারেশন অপশন")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        # একজন ইউজার একই প্রোডাক্টে একাধিক রিভিউ দিতে পারবেন না
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"






class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        # একজন ইউজার একই পণ্য একাধিকবার তালিকায় রাখতে পারবেন না
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"