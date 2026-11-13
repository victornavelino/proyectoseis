export interface DiasSemana {
  id: number
  lunes: boolean
  martes: boolean
  miercoles: boolean
  jueves: boolean
  viernes: boolean
  sabado: boolean
  domingo: boolean
  dias_texto: string
}
export type DiasSemanaInput = Omit<DiasSemana, 'id' | 'dias_texto'>

export interface PromocionArticulo {
  id: number
  promocion: number
  articulo: number
  articulo_nombre: string
  articulo_codigo: string
  valor: string
}
export type PromocionArticuloInput = Omit<PromocionArticulo, 'id' | 'articulo_nombre' | 'articulo_codigo'>

export interface Promocion {
  id: number
  nombre: string
  fecha_inicio: string
  fecha_fin: string
  es_por_precio: boolean
  porcentaje_todos: string | null
  dias_semana: number
  dias_semana_detalle: DiasSemana
  habilitada: boolean
  prioridad: number
  sucursal: number | null
  sucursal_nombre: string | null
  observaciones: string | null
  articulos: PromocionArticulo[]
}
export type PromocionInput = Pick<
  Promocion,
  'nombre' | 'fecha_inicio' | 'fecha_fin' | 'es_por_precio' | 'porcentaje_todos' | 'dias_semana' | 'habilitada' | 'prioridad' | 'sucursal' | 'observaciones'
>

export interface Descuento {
  id: number
  nombre: string
  valor: number
}
export type DescuentoInput = Omit<Descuento, 'id'>
