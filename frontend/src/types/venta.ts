export interface VentaArticulo {
  id: number
  articulo: number
  articulo_codigo: string
  nombre_articulo: string
  codigo_articulo: string
  cantidad_peso: string
  precio_unitario: string
  precio_promocion: string
  total_articulo: string
}

export interface Venta {
  numero_ticket: number
  fecha: string
  monto: string
  descuento: string
  anulado: boolean
  cobrada: boolean
  sucursal: number
  sucursal_nombre: string
  cliente: number
  cliente_nombre: string
  empleado: number
  empleado_nombre: string
  usuario: number
  usuario_username: string
  articulos: VentaArticulo[]
}

/** Línea del carrito en el frontend, antes de mandarla al backend. */
export interface ItemCarrito {
  /** id local, sólo para la key de React / poder borrar la línea. */
  clave: string
  articuloId: number
  articuloNombre: string
  articuloCodigo: string
  esPorPeso: boolean
  cantidadPeso: string
}

export interface ItemVentaInput {
  articulo: number
  cantidad_peso: string
}

export interface CrearVentaInput {
  empleado: number
  cliente: number
  articulos: ItemVentaInput[]
}

export interface ItemPrevisualizado {
  articulo: number
  articulo_nombre: string
  cantidad_peso: string
  precio_unitario: string
  precio_promocion: string
  total_articulo: string
}

export interface VentaPrevisualizada {
  articulos: ItemPrevisualizado[]
  monto: string
}
