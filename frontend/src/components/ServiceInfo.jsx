// Información clara sobre el servicio de atención (CA5 OM3-19)
export default function ServiceInfo({ info, compact = false }) {
  if (!info) return null
  return (
    <aside className={`service ${compact ? 'service--compact' : ''}`}>
      {!compact && (
        <>
          <h2>{info.title}</h2>
          <p>{info.description}</p>
          <ol className="service-steps">
            {info.how_it_works.map((step) => <li key={step}>{step}</li>)}
          </ol>
          <p className="tiny"><strong>Horario:</strong> {info.hours}</p>
        </>
      )}
      <h3>{compact ? '¿Necesitas ayuda inmediata?' : 'Líneas de atención 24 horas'}</h3>
      <ul className="lines">
        {info.lines.map((line) => (
          <li key={line.phone}>
            <a href={`tel:${line.phone}`} className="line">
              <span className="line-phone">{line.display ?? line.phone}</span>
              <span>
                <strong>{line.name}</strong>
                <span className="tiny">{line.detail}</span>
              </span>
            </a>
          </li>
        ))}
      </ul>
      <p className="tiny service-disclaimer">{info.disclaimer}</p>
    </aside>
  )
}
