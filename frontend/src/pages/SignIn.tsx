import React, { useState } from 'react'
import { api } from '../api'
import { useNavigate } from 'react-router-dom'

export function SignIn() {
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await api.login(email, password)
      nav('/groups/new')
    } catch (err: any) {
      setError(err?.message || 'Login failed')
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Sign In</h1>
        <p className="page-subtitle">Access your account to manage groups</p>
      </div>
      
      <div className="card">
        <form onSubmit={onSubmit}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input 
              className="form-input"
              value={email} 
              onChange={e => setEmail(e.target.value)} 
              type="email" 
              placeholder="you@example.com" 
              required 
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">Password</label>
            <input 
              className="form-input"
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              type="password" 
              placeholder="••••••••"
              required 
            />
          </div>
          
          <button type="submit" className="btn btn-primary btn-large">
            ⚡ Sign In
          </button>
        </form>
        
        {error && <div role="alert" className="alert alert-error">{error}</div>}
      </div>
    </div>
  )
}
