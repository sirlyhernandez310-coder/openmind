import Blob from './Blob'
import Logo from './Logo'
import LoopPattern from './LoopPattern'
import MindHeart from './MindHeart'

// Pantallas de acceso: panel lila ilustrado a la izquierda y formulario a la derecha
export default function AuthLayout({ title, subtitle, mood, children, footer, wide = false }) {
  return (
    <div className="auth">
      <aside className="auth-art panel-lilac">
        <LoopPattern variant="tall" width={34} />
        <Logo size="md" />
        <MindHeart className="auth-illustration" />
        <div className="auth-art-copy">
          <h2>Cuando mente y corazón se escuchan.</h2>
          <p>Evalúa cómo te sientes, mira tu evolución y habla con un psicólogo cuando lo necesites.</p>
        </div>
      </aside>

      <main className="auth-main">
        <div className={`auth-card ${wide ? 'auth-card--wide' : ''}`}>
          <div className="auth-card-mobile-logo"><Logo size="md" /></div>
          {mood && <Blob mood={mood} size={84} limbs={false} className="auth-card-blob float" />}
          <h1>{title}</h1>
          {subtitle && <p className="muted auth-subtitle">{subtitle}</p>}
          {children}
          {footer && <div className="auth-footer">{footer}</div>}
        </div>
      </main>
    </div>
  )
}
