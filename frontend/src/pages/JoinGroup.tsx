import React, { useState } from 'react'
import { api } from '../api'
import { useNavigate } from 'react-router-dom'
import { getToken, clearToken } from '../utils/storage'
import { ServicesToggle } from '../components/ServicesToggle'

export function JoinGroup() {
  const nav = useNavigate()
  const [code, setCode] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [services, setServices] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      const token = getToken()
      let res: any
      if (token) {
        try {
          const who = await api.whoami()
          if (who?.kind === 'participant') {
            const ok = window.confirm('You are already in a group. Leave or disband it before joining another?')
            if (!ok) return
            await api.leaveCurrent()
            clearToken()
            res = await api.joinGroupGuest(code, displayName, services.length ? services : undefined)
          } else {
            res = await api.joinGroupAsUser(code)
          }
        } catch {
          // token invalid -> treat as guest
          res = await api.joinGroupGuest(code, displayName, services.length ? services : undefined)
        }
      } else {
        res = await api.joinGroupGuest(code, displayName, services.length ? services : undefined)
      }
      const gcode = res?.group?.code || code
      nav(`/g/${gcode}`)
    } catch (err: any) {
      setError(err?.message || 'Failed to join')
    }
  }

  return (
    <div style={{ maxWidth: 520 }}>
      <h3>Join a Group</h3>
      <form onSubmit={onSubmit}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <label>
            Group Code
            <input value={code} onChange={e => setCode(e.target.value.toUpperCase())} required placeholder="ABC123" />
          </label>
          {!getToken() && (
            <>
              <label>
                Display name
                <input value={displayName} onChange={e => setDisplayName(e.target.value)} required placeholder="Your name" />
              </label>
              <ServicesToggle value={services} onChange={setServices} />
            </>
          )}
          <button type="submit">Join</button>
        </div>
      </form>
      {error && <div role="alert" style={{ color: 'crimson', marginTop: 8 }}>{error}</div>}
    </div>
  )
}
