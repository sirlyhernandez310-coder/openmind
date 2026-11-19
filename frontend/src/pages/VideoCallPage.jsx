import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { appointmentsApi } from '../api/appointments'
import Alert from '../components/Alert'
import Avatar from '../components/Avatar'
import Blob from '../components/Blob'
import Icon from '../components/Icon'
import { useAuth } from '../context/auth-context'
import { formatLongDay, formatTime, formatTimeRange } from '../format'

const POLL_MS = 1500
const ICE_WAIT_MS = 4000

// Espera a que el navegador termine de reunir sus "rutas" de conexión (ICE) antes de enviar la descripción
function waitForIce(pc) {
  if (pc.iceGatheringState === 'complete') return Promise.resolve()
  return new Promise((resolve) => {
    const done = () => {
      pc.removeEventListener('icegatheringstatechange', check)
      resolve()
    }
    const check = () => pc.iceGatheringState === 'complete' && done()
    pc.addEventListener('icegatheringstatechange', check)
    setTimeout(done, ICE_WAIT_MS)
  })
}

async function getMedia() {
  try {
    return await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: true })
  } catch {
    // sin cámara: se intenta solo con micrófono
    return navigator.mediaDevices.getUserMedia({ audio: true })
  }
}

/**
 * OM3-20 Videollamada.
 * El audio y el video viajan directo entre los dos navegadores (WebRTC).
 * La API solo intercambia la oferta del psicólogo y la respuesta del paciente.
 */
export default function VideoCallPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const isPsychologist = user.role === 'PSICOLOGO'
  const [info, setInfo] = useState(null)
  const [phase, setPhase] = useState('lobby') // lobby · joining · waiting · connecting · connected · ended
  const [error, setError] = useState('')
  const [micOn, setMicOn] = useState(true)
  const [camOn, setCamOn] = useState(true)
  const [hasVideo, setHasVideo] = useState(true)

  const localVideo = useRef(null)
  const remoteVideo = useRef(null)
  const stream = useRef(null)
  const pc = useRef(null)
  const iceServers = useRef([])
  const handled = useRef({ offerAt: null, answerAt: null, joinedAt: null })
  const busy = useRef(false)
  const phaseRef = useRef(phase)
  phaseRef.current = phase

  useEffect(() => {
    appointmentsApi.call(id).then(setInfo).catch((err) => setError(err.status === 404 ? 'No encontramos esta sesión entre las tuyas.' : err.message))
  }, [id])

  const closePeer = () => {
    pc.current?.close()
    pc.current = null
    if (remoteVideo.current) remoteVideo.current.srcObject = null
  }

  const newPeer = useCallback(() => {
    closePeer()
    const peer = new RTCPeerConnection({ iceServers: iceServers.current })
    stream.current.getTracks().forEach((track) => peer.addTrack(track, stream.current))
    peer.ontrack = (event) => {
      if (remoteVideo.current && remoteVideo.current.srcObject !== event.streams[0]) {
        remoteVideo.current.srcObject = event.streams[0]
      }
    }
    peer.onconnectionstatechange = () => {
      if (peer !== pc.current) return
      if (peer.connectionState === 'connected') setPhase('connected')
      if (['disconnected', 'failed'].includes(peer.connectionState)) setPhase('connecting')
    }
    pc.current = peer
    return peer
  }, [])

  // Psicólogo: crea la oferta (descripción de su audio/video y rutas de conexión) y la envía
  const sendOffer = useCallback(async () => {
    const peer = newPeer()
    await peer.setLocalDescription(await peer.createOffer())
    await waitForIce(peer)
    const state = await appointmentsApi.callSignal(id, 'offer', peer.localDescription.sdp)
    handled.current.offerAt = state.offer_at
    handled.current.answerAt = null
  }, [id, newPeer])

  // Paciente: recibe la oferta, crea su respuesta y la envía
  const sendAnswer = useCallback(async (offer) => {
    const peer = newPeer()
    await peer.setRemoteDescription({ type: 'offer', sdp: offer })
    await peer.setLocalDescription(await peer.createAnswer())
    await waitForIce(peer)
    await appointmentsApi.callSignal(id, 'answer', peer.localDescription.sdp)
  }, [id, newPeer])

  const tick = useCallback(async () => {
    if (busy.current) return
    busy.current = true
    try {
      const state = await appointmentsApi.call(id)
      if (!state.can_join) {
        setError(state.reason)
        return
      }
      const connected = phaseRef.current === 'connected'
      if (isPsychologist) {
        const patientIn = state.patient_joined_at
        if (!patientIn) {
          if (connected) closePeer()
          setPhase('waiting')
        } else if (!state.offer_at || Date.parse(patientIn) > Date.parse(state.offer_at)) {
          // el paciente entró (o volvió a entrar) después de la última oferta: se ofrece de nuevo
          setPhase('connecting')
          await sendOffer()
        } else if (state.answer && state.answer_at !== handled.current.answerAt && pc.current?.signalingState === 'have-local-offer') {
          handled.current.answerAt = state.answer_at
          await pc.current.setRemoteDescription({ type: 'answer', sdp: state.answer })
        }
      } else if (!state.psychologist_joined_at) {
        if (connected) closePeer()
        setPhase('waiting')
      } else if (
        state.offer && state.offer_at !== handled.current.offerAt
        && Date.parse(state.offer_at) >= Date.parse(handled.current.joinedAt)
      ) {
        handled.current.offerAt = state.offer_at
        setPhase('connecting')
        await sendAnswer(state.offer)
      } else if (!connected && !state.offer) {
        setPhase('waiting')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      busy.current = false
    }
  }, [id, isPsychologist, sendAnswer, sendOffer])

  useEffect(() => {
    if (!['waiting', 'connecting', 'connected'].includes(phase)) return undefined
    const timer = setInterval(tick, POLL_MS)
    return () => clearInterval(timer)
  }, [phase, tick])

  const stopEverything = useCallback(() => {
    closePeer()
    stream.current?.getTracks().forEach((track) => track.stop())
    stream.current = null
  }, [])

  // al salir de la página se cuelga la llamada
  useEffect(() => () => {
    if (stream.current) appointmentsApi.callSignal(id, 'leave').catch(() => {})
    stopEverything()
  }, [id, stopEverything])

  const join = async () => {
    setError('')
    setPhase('joining')
    try {
      stream.current = await getMedia()
    } catch {
      setPhase('lobby')
      setError('Necesitamos permiso para usar tu cámara y tu micrófono. Revisa el candado de la barra de direcciones.')
      return
    }
    setHasVideo(stream.current.getVideoTracks().length > 0)
    if (localVideo.current) localVideo.current.srcObject = stream.current
    try {
      const state = await appointmentsApi.callSignal(id, 'join')
      iceServers.current = state.ice_servers
      handled.current = { offerAt: null, answerAt: null, joinedAt: isPsychologist ? state.psychologist_joined_at : state.patient_joined_at }
      setPhase('waiting')
      await tick()
    } catch (err) {
      stopEverything()
      setPhase('lobby')
      setError(err.message)
    }
  }

  const hangUp = async () => {
    await appointmentsApi.callSignal(id, 'leave').catch(() => {})
    stopEverything()
    setPhase('ended')
  }

  const toggle = (kind) => {
    const tracks = kind === 'audio' ? stream.current?.getAudioTracks() : stream.current?.getVideoTracks()
    tracks?.forEach((track) => { track.enabled = !track.enabled })
    if (kind === 'audio') setMicOn((on) => !on)
    else setCamOn((on) => !on)
  }

  const backTo = isPsychologist ? '/psicologo/agenda' : '/paciente/sesiones'
  const appointment = info?.appointment
  const other = appointment && (isPsychologist ? appointment.patient : appointment.psychologist)
  const inCall = ['joining', 'waiting', 'connecting', 'connected'].includes(phase)

  if (!info) {
    return (
      <div className="stack">
        <Link to={backTo} className="back-link"><Icon name="back" size={18} /> Volver a mis sesiones</Link>
        {error ? <Alert>{error}</Alert> : <p className="muted">Preparando la videollamada…</p>}
      </div>
    )
  }

  const STATUS = {
    joining: 'Activando tu cámara y micrófono…',
    waiting: `Esperando a que ${other.first_name ?? other.full_name.split(' ')[0]} se conecte…`,
    connecting: 'Conectando…',
    connected: 'Conectados',
  }

  return (
    <div className="stack">
      <Link to={backTo} className="back-link"><Icon name="back" size={18} /> Volver a mis sesiones</Link>

      <header className="call-head">
        <Avatar user={other} size={56} />
        <div>
          <span className="eyebrow">Sesión virtual</span>
          <h1>{other.full_name}</h1>
          <p className="muted">{formatLongDay(appointment.start)} · {formatTimeRange(appointment.start, appointment.end)}</p>
        </div>
      </header>

      <Alert>{error}</Alert>

      {phase === 'ended' ? (
        <section className="card empty">
          <Blob mood="calma" size={120} />
          <h2>Saliste de la videollamada</h2>
          <p className="muted">Puedes volver a entrar mientras la sesión siga en curso.</p>
          <div className="hero-actions">
            <button type="button" className="btn btn--primary" onClick={() => setPhase('lobby')}>Volver a entrar</button>
            <Link to={backTo} className="btn btn--ghost">Ir a mis sesiones</Link>
          </div>
        </section>
      ) : (
        <section className={`call-stage ${phase === 'connected' ? 'call-stage--live' : ''}`}>
          <video ref={remoteVideo} className="call-remote" autoPlay playsInline />
          {phase !== 'connected' && (
            <div className="call-overlay">
              {inCall ? <Avatar user={other} size={110} /> : <Blob mood="alegria" size={120} className="float" />}
              {inCall ? (
                <p className="call-status"><span className="call-dot" /> {STATUS[phase]}</p>
              ) : info.can_join ? (
                <>
                  <h2>¿Todo listo para tu sesión?</h2>
                  <p>Al entrar, el navegador te pedirá permiso para usar la cámara y el micrófono.</p>
                  <button type="button" className="btn btn--sun" onClick={join}>
                    <Icon name="video" size={20} /> Entrar a la videollamada
                  </button>
                </>
              ) : (
                <>
                  <h2>Aún no puedes entrar</h2>
                  <p>{info.reason}</p>
                  {new Date(info.opens_at) > new Date() && (
                    <p className="call-status">Se habilita el {formatLongDay(info.opens_at)} a las {formatTime(info.opens_at)}</p>
                  )}
                </>
              )}
            </div>
          )}
          {phase === 'connected' && <span className="call-live"><span className="call-dot" /> En llamada</span>}

          <div className={`call-self ${inCall ? '' : 'call-self--hidden'}`}>
            <video ref={localVideo} autoPlay playsInline muted />
            {(!camOn || !hasVideo) && <div className="call-self-off"><Avatar user={user} size={48} /></div>}
          </div>

          {inCall && (
            <div className="call-controls">
              <button type="button" className={`call-btn ${micOn ? '' : 'call-btn--off'}`} onClick={() => toggle('audio')}
                aria-label={micOn ? 'Silenciar micrófono' : 'Activar micrófono'} title={micOn ? 'Silenciar' : 'Activar micrófono'}>
                <Icon name={micOn ? 'mic' : 'micOff'} size={22} />
              </button>
              {hasVideo && (
                <button type="button" className={`call-btn ${camOn ? '' : 'call-btn--off'}`} onClick={() => toggle('video')}
                  aria-label={camOn ? 'Apagar cámara' : 'Encender cámara'} title={camOn ? 'Apagar cámara' : 'Encender cámara'}>
                  <Icon name={camOn ? 'video' : 'videoOff'} size={22} />
                </button>
              )}
              <button type="button" className="call-btn call-btn--hangup" onClick={hangUp} aria-label="Colgar" title="Colgar">
                <Icon name="hangup" size={24} />
              </button>
            </div>
          )}
        </section>
      )}

      <p className="muted tiny center">
        <Icon name="lock" size={14} /> El audio y el video viajan cifrados directamente entre tu navegador y el de {other.full_name.split(' ')[0]}; no se graban.
      </p>
    </div>
  )
}
