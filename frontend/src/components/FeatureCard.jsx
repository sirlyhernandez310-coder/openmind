import { Link } from 'react-router-dom'
import Icon from './Icon'

// tone: sun | coral | white | lilac
export default function FeatureCard({ icon, title, children, tone = 'white', soon = false, to, cta, highlight = false }) {
  const content = (
    <>
      <span className={`feature-icon ${tone === 'white' ? 'feature-icon--mint' : ''}`}><Icon name={icon} size={24} /></span>
      <h3>{title}</h3>
      <p>{children}</p>
      {soon && <span className="badge">Próximo sprint</span>}
      {cta && <span className={`feature-cta ${highlight ? 'feature-cta--alert' : ''}`}>{cta} <Icon name="arrow" size={16} /></span>}
    </>
  )
  if (to) return <Link to={to} className={`feature feature--${tone}`}>{content}</Link>
  return <article className={`feature feature--${tone} feature--static`}>{content}</article>
}
