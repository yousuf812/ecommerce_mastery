# store/utils.py
from io import BytesIO
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    """HTML টেমপ্লেট ও ডেটা কনটেক্সট গ্রহণ করে PDF রেসপন্স তৈরি করে"""
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    
    # UTF-8 এনকোডিংয়ে PDF তৈরি
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, encoding='UTF-8')
    
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None