# store/forms.py
from django import forms
from .models import Order, Review

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'city', 'postal_code']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:border-indigo-500 focus:outline-none transition', 'placeholder': 'উদা: মো: তানভীর'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:border-indigo-500 focus:outline-none transition', 'placeholder': 'উদা: হাসান'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:border-indigo-500 focus:outline-none transition', 'placeholder': 'yourname@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:border-indigo-500 focus:outline-none transition', 'placeholder': '০১৭XXXXXXXX'}),
            'address': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:border-indigo-500 focus:outline-none transition', 'placeholder': 'রোড নং, বাড়ি/ফ্ল্যাট নং, এলাকা'}),
            'city': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:border-indigo-500 focus:outline-none transition', 'placeholder': 'ঢাকা/চট্টগ্রাম/খুলনা'}),
            'postal_code': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:border-indigo-500 focus:outline-none transition', 'placeholder': 'পোস্টাল কোড (ঐচ্ছিক)'}),
        }


class CouponApplyForm(forms.Form):
    code = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'প্রমো বা কুপন কোড লিখুন',
            'class': 'w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-indigo-500 uppercase font-semibold'
        })
    )





class ReviewForm(forms.ModelForm):
    RATING_CHOICES = [
        (5, '★★★★★ (৫/৫ - চমৎকার)'),
        (4, '★★★★☆ (৪/৫ - ভালো)'),
        (3, '★★★☆☆ (৩/৫ - সন্তোষজনক)'),
        (2, '★★☆☆☆ (২/৫ - চলনসই)'),
        (1, '★☆☆☆☆ (১/৫ - খারাপ)'),
    ]

    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold focus:bg-white focus:border-indigo-500 focus:outline-none transition'
        })
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:border-indigo-500 focus:outline-none transition',
                'rows': 4,
                'placeholder': 'পণ্যটির ব্যবহারিক অভিজ্ঞতা কেমন ছিল? ডেলিভারি ও প্যাকেজিং কেমন হয়েছে বিস্তারিত লিখুন...'
            }),
        }