export interface Sucursal {
  id: number
  nombre: string
  domicilio: string
}
export type SucursalInput = Omit<Sucursal, 'id'>

export interface Empleado {
  id: number
  persona: number
  persona_nombre: string
  cuil: string
  fecha_baja: string | null
  activo: boolean
}
export interface EmpleadoInput {
  persona: number
  cuil: string
  fecha_baja: string | null
}
