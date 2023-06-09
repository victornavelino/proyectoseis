from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from util.models import  Telefono


class TelefonoInline(GenericTabularInline):
    model = Telefono
    extra = 1

