import React, { useState } from 'react'
import { api } from '../api'
import { useNavigate } from 'react-router-dom'
import { getToken } from '../utils/storage'

export function JoinGroup() {
  const nav = useNavigate()
  const [code, setCode] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [servicesText, setServicesText] = useState('')
  const [error, setError] = useState<string | null>(null)

  function parseServices(input: string): string[] | undefined {
    const arr = input.split(',').map(s => s.trim().toLowerCase()).filter(Boolean)
    return arr.length ? arr : undefined
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      const token = getToken()
      const res = token
        ? await api.joinGroupAsUser(code)
        : await api.joinGroupGuest(code, displayName, parseServices(servicesText))
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
              <label>
                Streaming services (comma separated, optional)
                <input value={servicesText} onChange={e => setServicesText(e.target.value)} placeholder="netflix, hulu, amazon, hbo" />
              </label>
            </>
          )}
          <button type="submit">Join</button>
        </div>
      </form>
      {error && <div role="alert" style={{ color: 'crimson', marginTop: 8 }}>{error}</div>}
    </div>
  )
}
