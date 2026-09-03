import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode, type RefObject } from 'react'
import { Loader, Paper, Stack, Text, TextInput, UnstyledButton } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'

interface Props<T> {
  placeholder: string
  buscar: (query: string) => Promise<T[]>
  renderItem: (item: T) => ReactNode
  onSeleccionar: (item: T) => void
  clave: (item: T) => string | number
  minCaracteres?: number
  /** Adónde mover el foco después de seleccionar un resultado (con Enter o clic) — pensado para
   * saltar al siguiente campo del formulario sin soltar el teclado (ej. de "Cliente" a
   * "Empleado" en VentaNuevaPage). Si no se pasa, el foco vuelve al propio input de búsqueda
   * (lo natural cuando este buscador se usa para agregar varios ítems seguidos, ej. artículos). */
  enfocarSiguienteRef?: RefObject<HTMLInputElement | null>
}

/** Buscador genérico: texto + lista de resultados navegable con flechas ↑/↓ y Enter (además de
 * clic). Se usa para cliente/artículo en el punto de venta — no usa el Autocomplete de Mantine
 * para tener control directo sobre el fetch async (debounce + cancelación de resultados viejos)
 * sin pelear con su API de datos asíncronos. */
export default function BuscadorLista<T>({
  placeholder,
  buscar,
  renderItem,
  onSeleccionar,
  clave,
  minCaracteres = 2,
  enfocarSiguienteRef,
}: Props<T>) {
  const [texto, setTexto] = useState('')
  const [textoDebounced] = useDebouncedValue(texto, 300)
  const [resultados, setResultados] = useState<T[]>([])
  const [cargando, setCargando] = useState(false)
  const [indiceActivo, setIndiceActivo] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (textoDebounced.trim().length < minCaracteres) {
      setResultados([])
      return
    }
    let cancelado = false
    setCargando(true)
    buscar(textoDebounced)
      .then((r) => {
        if (!cancelado) setResultados(r)
      })
      .finally(() => {
        if (!cancelado) setCargando(false)
      })
    return () => {
      cancelado = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [textoDebounced])

  // Primer resultado pre-seleccionado apenas llega la lista: así alcanza con tipear y apretar
  // Enter, sin tener que bajar con la flecha para el caso más común (el que buscabas es el
  // primero).
  useEffect(() => {
    setIndiceActivo(resultados.length > 0 ? 0 : -1)
  }, [resultados])

  const seleccionar = (item: T) => {
    onSeleccionar(item)
    setTexto('')
    setResultados([])
    if (enfocarSiguienteRef?.current) {
      enfocarSiguienteRef.current.focus()
    } else {
      inputRef.current?.focus()
    }
  }

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (resultados.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setIndiceActivo((i) => Math.min(i + 1, resultados.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setIndiceActivo((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && indiceActivo >= 0) {
      e.preventDefault()
      seleccionar(resultados[indiceActivo])
    }
  }

  return (
    <div>
      <TextInput
        ref={inputRef}
        placeholder={placeholder}
        value={texto}
        onChange={(e) => setTexto(e.currentTarget.value)}
        onKeyDown={onKeyDown}
        rightSection={cargando ? <Loader size="xs" /> : null}
      />
      {resultados.length > 0 && (
        <Paper withBorder mt={4} p={4} shadow="sm" style={{ maxHeight: 220, overflowY: 'auto' }}>
          <Stack gap={2}>
            {resultados.map((item, i) => (
              <UnstyledButton
                key={clave(item)}
                onClick={() => seleccionar(item)}
                onMouseEnter={() => setIndiceActivo(i)}
                p="xs"
                style={{
                  borderRadius: 4,
                  backgroundColor: i === indiceActivo ? 'var(--mantine-color-red-light)' : undefined,
                }}
              >
                {renderItem(item)}
              </UnstyledButton>
            ))}
          </Stack>
        </Paper>
      )}
      {textoDebounced.trim().length >= minCaracteres && !cargando && resultados.length === 0 && (
        <Text size="sm" c="dimmed" mt={4}>
          Sin resultados.
        </Text>
      )}
    </div>
  )
}
