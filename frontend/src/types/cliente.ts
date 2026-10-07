import type { Persona } from './persona'

export type CondicionIva = 'ri' | 'rn' | 'ex' | 'mo' | 'cf'

export interface Cliente {
  id: number
  persona: number
  persona_detalle: Persona
  condicion_iva: CondicionIva
  condicion_iva_display: string
  lista_precio: number | null
  lista_precio_nombre: string | null
  fecha_alta: string
}

export interface ClienteInput {
  persona: number
  condicion_iva: CondicionIva
  lista_precio: number | null
}
