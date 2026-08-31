export interface Perfil {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  is_staff: boolean
  sucursal: number | null
  sucursal_nombre: string | null
  groups: { id: number; name: string }[]
}
