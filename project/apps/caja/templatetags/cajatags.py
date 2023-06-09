from django import template
from django.contrib.admin.templatetags.admin_list import result_list as admin_list_result_list

from venta.models import Venta


def result_list(cl):
    ventas = Venta.objects.filter(cobrada=False)
    mycl = {'ventas': ventas}
    mycl.update(admin_list_result_list(cl))
    return mycl


register = template.Library()
register.inclusion_tag('change_list.html')(result_list)