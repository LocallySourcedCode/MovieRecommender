import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Swipe } from '../components/Swipe'
import { api } from '../api'

export function Movies() {
  const { code } = useParams()
  const nav = useNavigate()
  const [msg, setMsg] = useState<string | null>(null)
  const [isHost, setIsHost] = useState(false)

  if (!code) return <div>Missing group code</div>

  useEffect(() => {
    const anyApi: any = api as any
    if (typeof anyApi.whoami === 'function') {
      anyApi.whoami().then((w: any) => {
        const host = Boolean(w?.is_host)
        setIsHost(host)
      }).catch(() => setIsHost(false))
    } else {
      setIsHost(false)
    }
  }, [code])

  useEffect(() => {
    let active = true
    async function poll() {
      try {
        const p = await api.getProgress(code!)
        if (!active) return
        if (p.phase === 'genre_nomination') {
          nav(`/g/${code}/nominate-genres`)
        } else if (p.phase === 'setup') {
          nav(`/g/${code}`)
        }
      } catch {}
      if (active) setTimeout(poll, 3000)
    }
    poll()
    return () => { active = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code, nav])

  async function useVeto() {
    setMsg(null)
    try {
      const res = await api.useVeto(code!)
      if (res?.status === 'current') setMsg('Current movie vetoed. A new option is shown.')
    } catch (err: any) {
      setMsg(err?.message || 'Veto failed')
    }
  }

  return (
    <div className="page-container-wide">
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '2rem' }}>
        <button onClick={() => nav(`/g/${code}`)} className="btn btn-back">
          ← Back
        </button>
        <h1 style={{ flex: 1, textAlign: 'center', fontSize: '2rem', fontWeight: 700, color: 'white', margin: 0 }}>Movie Selection</h1>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={useVeto} className="btn btn-secondary">
            ⚡ Use Veto
          </button>
          {isHost && (
            <button 
              title="Restart movie recommendation process to genre nomination" 
              onClick={async ()=>{ try { await api.resetGenres(code!); nav(`/g/${code}/nominate-genres`) } catch(e){} }}
              className="btn btn-danger"
            >
              🔄 Restart
            </button>
          )}
        </div>
      </div>
      
      {msg && <div className="alert alert-info">{msg}</div>}
      <Swipe code={code} />
    </div>
  )
}
