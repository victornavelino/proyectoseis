export interface TipoIva {
  id: number
  nombre: string
  porcentaje: string
}
export type TipoIvaInput = Omit<TipoIva, 'id'>

export interface UnidadMedida {
  id: number
  nombre: string
  abreviatura: string
}
export type UnidadMedidaInput = Omit<UnidadMedida, 'id'>

export interface Categoria {
  id: number
  nombre: string
  nodo_padre: number | null
  tipo_iva: number
  tipo_iva_nombre: string
}
export type CategoriaInput = Omit<Categoria, 'id' | 'tipo_iva_nombre'>

export interface ListaPrecio {
  id: number
  nombre: string
}
export type ListaPrecioInput = Omit<ListaPrecio, 'id'>

export interface Articulo {
  id: number
  nombre: string
  abreviatura: string
  codigo: string
  categoria: number
  categoria_nombre: string
  unidad_medida: number
  unidad_medida_nombre: string
  es_por_peso: boolean
}

export type ArticuloInput = Omit<Articulo, 'id' | 'categoria_nombre' | 'unidad_medida_nombre'>

export interface Precio {
  id: number
  articulo: number
  articulo_nombre: string
  articulo_codigo: string
  sucursal: number
  sucursal_nombre: string
  lista_precio: number
  lista_precio_nombre: string
  precio: string
}
export type PrecioInput = Pick<Precio, 'articulo' | 'sucursal' | 'lista_precio' | 'precio'>
