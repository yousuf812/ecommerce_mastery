# store/emails.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_order_confirmation_email(order):
    """ক্রেতাকে অর্ডার নিশ্চিতকরণ HTML ইমেইল পাঠানো"""
    subject = f"অর্ডার নিশ্চিতকরণ - #{order.id} | NovaMart"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [order.email]

    context = {
        'order': order,
        'company_name': 'NovaMart',
        'support_email': 'support@novamart.com',
    }

    # HTML ও প্লেইন টেক্সট কনটেন্ট রেন্ডার
    html_content = render_to_string('store/emails/order_confirmation.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    email.attach_alternative(html_content, "text/html")
    
    try:
        email.send(fail_silently=False)
    except Exception as e:
        print(f"ইমেইল পাঠাতে ত্রুটি: {e}")


def send_low_stock_alert_email(product):
    """পণ্যের স্টক কমে গেলে অ্যাডমিনকে অ্যালার্ট ইমেইল পাঠানো"""
    subject = f"⚠️ [জরুরি] কম স্টক অ্যালার্ট: {product.name}"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [settings.ADMIN_ALERT_EMAIL]

    context = {
        'product': product,
        'threshold': settings.LOW_STOCK_THRESHOLD,
    }

    html_content = render_to_string('store/emails/low_stock_alert.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    email.attach_alternative(html_content, "text/html")

    try:
        email.send(fail_silently=False)
    except Exception as e:
        print(f"স্টক অ্যালার্ট পাঠাতে ত্রুটি: {e}")