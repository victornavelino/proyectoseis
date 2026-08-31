import { useEffect, useState, type ReactNode } from 'react'
import { Loader, Paper, Stack, Text, TextInput, UnstyledButton } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'

interface Props<T> {
  placeholder: string
  buscar: (query: string) => Promise<T[]>
  renderItem: (item: T) => ReactNode
  onSeleccionar: (item: T) => void
  clave: (item: T) => string | number
  minCaracteres?: number
}

/** Buscador genérico: texto + lista de resultados clickeables debajo. Se usa para
 * cliente/artículo en el punto de venta — no usa el Autocomplete de Mantine para tener control
 * directo sobre el fetch async (debounce + cancelación de resultados viejos) sin pelear con su
 * API de datos asíncronos. */
export default function BuscadorLista<T>({
  placeholder,
  buscar,
  renderItem,
  onSeleccionar,
  clave,
  minCaracteres = 2,
}: Props<T>) {
  const [texto, setTexto] = useState('')
  const [textoDebounced] = useDebouncedValue(texto, 300)
  const [resultados, setResultados] = useState<T[]>([])
  const [cargando, setCargando] = useState(false)

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

  return (
    <div>
      <TextInput
        placeholder={placeholder}
        value={texto}
        onChange={(e) => setTexto(e.currentTarget.value)}
        rightSection={cargando ? <Loader size="xs" /> : null}
      />
      {resultados.length > 0 && (
        <Paper withBorder mt={4} p={4} shadow="sm" style={{ maxHeight: 220, overflowY: 'auto' }}>
          <Stack gap={2}>
            {resultados.map((item) => (
              <UnstyledButton
                key={clave(item)}
                onClick={() => {
                  onSeleccionar(item)
                  setTexto('')
                  setResultados([])
                }}
                p="xs"
                style={{ borderRadius: 4 }}
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
