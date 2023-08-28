import json

from django.contrib import messages
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from cuentacorriente.models import CuentaCorriente
from project.apps.cuentacorriente.utils import calcular_saldo_cc


def get_cc_cliente(request, cliente_id):
    if request.user.is_authenticated:
        if request.method == 'GET':
            print("id cliente")
            print(cliente_id)
            try:
                cuenta_corriente = CuentaCorriente.objects.get(cliente_id=cliente_id, activa=True)
                print(cuenta_corriente.cliente)
                saldo_cc=calcular_saldo_cc(cuenta_corriente)
                data = {"id": cuenta_corriente.pk,
                        "cliente": cuenta_corriente.cliente.persona.obtener_nombre_completo(),
                        "tope": str(cuenta_corriente.tope),
                        "activa": cuenta_corriente.activa,
                        "fecha": str(cuenta_corriente.fecha),
                        "saldo_cc": str(saldo_cc)
                        }
            except ObjectDoesNotExist:
                data = {'error': 'El cliente No tiene Cuenta Corrientesdsdsdsd'}
            print('imprimiento cdata')
            print(data)
            data = json.dumps(data)
            return HttpResponse(data, content_type="application/json")
