import { Isotipo } from './Logo'
import LoopPattern from './LoopPattern'

// Pantalla de carga con el logo animado (se muestra al abrir la app)
export default function Splash({ leaving = false }) {
  return (
    <div className={`splash ${leaving ? 'splash--leaving' : ''}`} role="status" aria-label="Cargando Open Mind">
      <LoopPattern variant="tall" animated />
      <div className="splash-content">
        <Isotipo size={140} animated />
        <span className="splash-word">Open Mind</span>
        <span className="splash-tag">Tu mente, en buenas manos</span>
      </div>
    </div>
  )
}
