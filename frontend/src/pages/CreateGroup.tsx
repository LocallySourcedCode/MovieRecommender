import React, { useState } from 'react'
import { api } from '../api'
import { useNavigate } from 'react-router-dom'
import { ServicesToggle } from '../components/ServicesToggle'

export function CreateGroup() {
  const nav = useNavigate()
  const [displayName, setDisplayName] = useState('')
  const [services, setServices] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)

  async function onCreateGuest(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setCreating(true)
    try {
      // If currently holding a participant token, prompt to leave/disband first
      try {
        const who = await api.whoami()
        if (who?.kind === 'participant') {
          const ok = window.confirm('You are already in a group. Leave or disband it to create a new one?')
          if (!ok) { setCreating(false); return }
          await api.leaveCurrent()
          // token will be invalid after leaving; api.createGroupGuest skips auth anyway
        }
      } catch {
        // not signed in or invalid token -> ignore
      }
      const res = await api.createGroupGuest(displayName, services.length ? services : undefined)
      const code = res?.group?.code
      if (code) nav(`/g/${code}/nominate-genres`)
    } catch (err: any) {
      setError(err?.message || 'Failed to create group')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div style={{ maxWidth: 520 }}>
      <h3>Create a Group (Guest)</h3>
      <form onSubmit={onCreateGuest}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <label>
            Display name (for guests)
            <input value={displayName} onChange={e => setDisplayName(e.target.value)} required placeholder="Your name" />
          </label>
          <ServicesToggle value={services} onChange={setServices} />
          <button type="submit" disabled={creating}>Create Group</button>
        </div>
      </form>
      {error && <div role="alert" style={{ color: 'crimson', marginTop: 8 }}>{error}</div>}
      <p style={{ marginTop: 16 }}>
        If you are signed in as a user, you can also create a group from your account; use the Sign In link above first.
      </p>
    </div>
  )
}
