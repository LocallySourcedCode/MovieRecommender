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
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Join a Group</h1>
        <p className="page-subtitle">Enter a group code to join an existing session</p>
      </div>
      
      <div className="card">
        <form onSubmit={onSubmit}>
          <div className="form-group">
            <label className="form-label">Group Code</label>
            <input 
              className="form-input"
              value={code} 
              onChange={e => setCode(e.target.value.toUpperCase())} 
              required 
              placeholder="ABC123" 
              style={{ textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}
            />
          </div>
          
          {!getToken() && (
            <>
              <div className="form-group">
                <label className="form-label">Display Name</label>
                <input 
                  className="form-input"
                  value={displayName} 
                  onChange={e => setDisplayName(e.target.value)} 
                  required 
                  placeholder="Your name" 
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Streaming Services (Optional)</label>
                <ServicesToggle value={services} onChange={setServices} />
              </div>
            </>
          )}
          
          <button type="submit" className="btn btn-primary btn-large">
            🚀 Join Group
          </button>
        </form>
        
        {error && <div role="alert" className="alert alert-error">{error}</div>}
      </div>
    </div>
  )
}
