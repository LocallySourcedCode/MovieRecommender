import React, { useState } from 'react'
import { api } from '../api'
import { useNavigate } from 'react-router-dom'

function parseServices(input: string): string[] | undefined {
  const arr = input.split(',').map(s => s.trim().toLowerCase()).filter(Boolean)
  return arr.length ? arr : undefined
}

export function CreateGroup() {
  const nav = useNavigate()
  const [displayName, setDisplayName] = useState('')
  const [servicesText, setServicesText] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)

  async function onCreateGuest(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setCreating(true)
    try {
      const res = await api.createGroupGuest(displayName, parseServices(servicesText))
      const code = res?.group?.code
      if (code) nav(`/g/${code}`)
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
          <label>
            Streaming services (comma separated, optional)
            <input value={servicesText} onChange={e => setServicesText(e.target.value)} placeholder="netflix, hulu, amazon, hbo" />
          </label>
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
