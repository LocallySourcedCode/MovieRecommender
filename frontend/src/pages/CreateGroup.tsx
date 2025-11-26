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
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Create a Group</h1>
        <p className="page-subtitle">Start a new movie selection session with your friends</p>
      </div>
      
      <div className="card">
        <form onSubmit={onCreateGuest}>
          <div className="form-group">
            <label className="form-label">Display Name</label>
            <input 
              className="form-input"
              value={displayName} 
              onChange={e => setDisplayName(e.target.value)} 
              required 
              placeholder="Enter your name" 
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">Streaming Services (Optional)</label>
            <ServicesToggle value={services} onChange={setServices} />
          </div>
          
          <button type="submit" disabled={creating} className="btn btn-primary btn-large">
            🎬 Create Group
          </button>
        </form>
        
        {error && <div role="alert" className="alert alert-error">{error}</div>}
        
        <div className="tip-box">
          <span className="tip-icon">💡</span>
          <p className="tip-text">
            Tip: If you are signed in as a user, you can also create a group from your account. Use the Sign In link above first.
          </p>
        </div>
      </div>
    </div>
  )
}
