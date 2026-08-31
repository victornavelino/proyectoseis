export interface Telefono {
  tipo: 'fax' | 'telefono' | 'celular'
  numero: string
}

export interface Persona {
  id: number
  nombre: string
  apellido: string
  documento_identidad: string
  fecha_nacimiento: string | null
  domicilio: string | null
  correo_electronico: string | null
  telefonos: Telefono[]
}

export type PersonaInput = Omit<Persona, 'id'>
