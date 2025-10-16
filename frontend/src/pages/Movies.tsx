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

  async function useVeto() {
    setMsg(null)
    try {
      const res = await api.useVeto(code)
      if (res?.status === 'current') setMsg('Current movie vetoed. A new option is shown.')
    } catch (err: any) {
      setMsg(err?.message || 'Veto failed')
    }
  }

  return (
    <div>
      <h3>Movies ({code})</h3>
      <div style={{ marginBottom: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
        <button onClick={useVeto}>Use Veto</button>
        {isHost && (
          <button title="Restart movie recommendation process to genre nomination" onClick={async ()=>{ try { await api.resetGenres(code!); nav(`/g/${code}/nominate-genres`) } catch(e){} }}>
            Restart
          </button>
        )}
        {msg && <span style={{ marginLeft: 8 }}>{msg}</span>}
      </div>
      <Swipe code={code} />
    </div>
  )
}
