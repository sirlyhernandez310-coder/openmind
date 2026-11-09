import { useEffect, useRef } from 'react'

// Ejecuta `callback` cada `delay` ms mientras `active` sea true (y la pestaña esté visible).
export default function usePolling(callback, delay, active = true) {
  const saved = useRef(callback)

  useEffect(() => {
    saved.current = callback
  }, [callback])

  useEffect(() => {
    if (!active) return undefined
    const tick = () => {
      if (document.visibilityState === 'visible') saved.current()
    }
    const id = setInterval(tick, delay)
    return () => clearInterval(id)
  }, [delay, active])
}
