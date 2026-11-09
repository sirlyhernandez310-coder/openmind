import Blob from './Blob'
import LoopPattern from './LoopPattern'

export default function PageHeader({ eyebrow, title, children, mood = 'calma', aside }) {
  return (
    <header className="page-header panel-lilac">
      <LoopPattern variant="wide" />
      <div className="page-header-text">
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h1>{title}</h1>
        {children && <p>{children}</p>}
      </div>
      {aside ?? <Blob mood={mood} size={130} className="float page-header-blob" />}
    </header>
  )
}
