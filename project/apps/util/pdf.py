from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML


def render_pdf_response(request, template, context=None, filename='documento.pdf', show_content_in_browser=True):
    """Renderiza `template` a PDF con WeasyPrint y lo devuelve como HttpResponse.

    Reemplaza a `wkhtmltopdf.views.PDFTemplateResponse` (paquete/binario dados
    de baja, ver requirements). Los márgenes que antes se pasaban vía
    `cmd_options` ahora se definen con reglas CSS `@page` dentro del propio
    template.
    """
    html_string = render_to_string(template, context or {}, request=request)
    pdf_bytes = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
    disposition = 'inline' if show_content_in_browser else 'attachment'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
    return response
