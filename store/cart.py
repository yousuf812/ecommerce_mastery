from decimal import Decimal
from django.conf import settings
from .models import Product, Coupon


CART_SESSION_ID = 'cart'

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        
        # সেশনে কার্ট না থাকলে নতুন ডিকশনারি ইনিশিয়ালাইজ করা
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """কার্টে প্রোডাক্ট যোগ বা সংখ্যা আপডেট করা"""
        product_id = str(product.id)
        current_price = product.discount_price if product.discount_price else product.price

        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(current_price)
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

    def remove(self, product):
        """কার্ট থেকে নির্দিষ্ট প্রোডাক্ট মুছে ফেলা"""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        # সেশন পরিবর্তন চিহ্নিত করা
        self.session.modified = True

    def __iter__(self):
        """লুপ চালানোর সময় ডেটাবেজ থেকে আসল প্রোডাক্ট অবজেক্ট এনে দেওয়া"""
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """কার্টে মোট কয়টি আইটেম আছে গণনা করা"""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """কার্টের সর্বমোট মূল্য হিসাব করা"""
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        """অর্ডার সম্পূর্ণ হলে কার্ট খালি করা"""
        del self.session[CART_SESSION_ID]
        self.save()



CART_SESSION_ID = 'cart'

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart
        # সেশন থেকে কুপন আইডি লোড করা
        self.coupon_id = self.session.get('coupon_id')

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        current_price = product.discount_price if product.discount_price else product.price

        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(current_price)
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_subtotal_price(self):
        """কোনো ছাড় ব্যতীত প্রাথমিক মোট মূল্য"""
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    @property
    def coupon(self):
        """সেশনে সংরক্ষিত সক্রিয় কুপন অবজেক্ট রিটার্ন করে"""
        if self.coupon_id:
            try:
                coupon = Coupon.objects.get(id=self.coupon_id)
                if coupon.is_valid():
                    return coupon
            except Coupon.DoesNotExist:
                pass
        return None

    def get_discount_amount(self):
        """কুপনের শতকরা হার অনুযায়ী কর্তনকৃত মূল্য"""
        if self.coupon:
            return (Decimal(self.coupon.discount) / Decimal(100)) * self.get_subtotal_price()
        return Decimal(0)

    def get_total_price(self):
        """ছাড় বাদ দেওয়ার পর চূড়ান্ত প্রদেয় মূল্য"""
        return self.get_subtotal_price() - self.get_discount_amount()

    def clear(self):
        del self.session[CART_SESSION_ID]
        if 'coupon_id' in self.session:
            del self.session['coupon_id']
        self.save()