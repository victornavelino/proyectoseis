import { apiFetch } from './client'
import type { Persona, PersonaInput } from '../types/persona'

export function crearPersona(datos: PersonaInput) {
  return apiFetch<Persona>('api/v1/persona/', { method: 'POST', body: datos })
}

/** Devuelve el id de la persona con ese documento, o null si no existe (usuario.api reutiliza
 * este mismo patrón de "buscar antes de crear" — persona.api.PersonaViewSet.obtener_persona_id). */
export async function buscarPersonaPorDocumento(documentoIdentidad: string): Promise<number | null> {
  const data = await apiFetch<{ persona_id: number | null }>('api/v1/persona/obtener_persona/', {
    method: 'POST',
    body: { documento_identidad: documentoIdentidad },
  })
  return data.persona_id
}

export function obtenerPersona(id: number) {
  return apiFetch<Persona>(`api/v1/persona/${id}/`)
}
