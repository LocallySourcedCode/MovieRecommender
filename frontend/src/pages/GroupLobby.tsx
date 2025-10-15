import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Swipe } from '../components/Swipe'
import { api } from '../api'

export function GroupLobby() {
  const { code } = useParams()
  const [error, setError] = useState<string | null>(null)
  const [vetoMessage, setVetoMessage] = useState<string | null>(null)

  if (!code) return <div>Missing group code</div>

  async function useVeto() {
    setVetoMessage(null)
    try {
      const res = await api.useVeto(code)
      if (res?.status === 'current') {
        setVetoMessage('Current movie vetoed. A new option is shown.')
      }
    } catch (err: any) {
      setError(err?.message || 'Veto failed')
    }
  }

  return (
    <div>
      <h3>Group Lobby ({code})</h3>
      <div style={{ marginBottom: 8 }}>
        <button onClick={useVeto}>Use Veto</button>
        {vetoMessage && <span style={{ marginLeft: 8 }}>{vetoMessage}</span>}
      </div>
      <Swipe code={code} />
      {error && <div role="alert" style={{ color: 'crimson', marginTop: 8 }}>{error}</div>}
    </div>
  )
}
