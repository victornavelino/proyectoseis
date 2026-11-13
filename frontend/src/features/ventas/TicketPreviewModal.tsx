import { useEffect, useRef, useState } from 'react'
import { Button, Group, Modal, Text } from '@mantine/core'
import { IconPrinter } from '@tabler/icons-react'

interface Props {
  opened: boolean
  numeroTicket: number | null
  /** Blob URL del PDF (ver api/venta.ts § imprimirTicket) — el caller es dueño de revocarlo. */
  url: string | null
  onClose: () => void
}

/** Vista previa del ticket recién generado, embebida en un iframe. Enter imprime sin soltar el
 * teclado (dispara el diálogo nativo del visor de PDF del navegador sobre ese iframe) — pensado
 * para el flujo de mostrador: confirmar venta → se abre esta vista → Enter → imprimir. */
export default function TicketPreviewModal({ opened, numeroTicket, url, onClose }: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const [cargado, setCargado] = useState(false)

  useEffect(() => {
    if (!opened) setCargado(false)
  }, [opened])

  const imprimir = () => {
    iframeRef.current?.contentWindow?.print()
  }

  useEffect(() => {
    if (!opened || !cargado) return
    // capture: true para ganarle a la acción por defecto del navegador (Enter activando el
    // botón enfocado dentro del modal) — sin esto podría "click-earse" Continuar en vez de
    // imprimir, según qué elemento haya quedado enfocado.
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        imprimir()
      }
    }
    window.addEventListener('keydown', onKeyDown, { capture: true })
    return () => window.removeEventListener('keydown', onKeyDown, { capture: true })
  }, [opened, cargado])

  return (
    <Modal opened={opened} onClose={onClose} title={`Ticket #${numeroTicket ?? ''}`} size="lg">
      <Text size="xs" c="dimmed" mb="xs">
        Enter para imprimir.
      </Text>
      {url && (
        <iframe
          ref={iframeRef}
          src={url}
          title="Vista previa del ticket"
          onLoad={() => setCargado(true)}
          style={{ width: '100%', height: '70vh', border: '1px solid var(--mantine-color-gray-3)' }}
        />
      )}
      <Group justify="flex-end" mt="md">
        <Button variant="default" onClick={onClose}>
          Continuar
        </Button>
        <Button color="red" leftSection={<IconPrinter size={16} />} disabled={!cargado} onClick={imprimir}>
          Imprimir
        </Button>
      </Group>
    </Modal>
  )
}
