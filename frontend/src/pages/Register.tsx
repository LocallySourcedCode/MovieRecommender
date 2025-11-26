import React, { useState } from 'react'
import { api } from '../api'
import { useNavigate } from 'react-router-dom'

export function Register() {
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    
    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }
    
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }
    
    try {
      await api.register(email, password)
      setSuccess(true)
      setTimeout(() => nav('/signin'), 2000)
    } catch (err: any) {
      setError(err?.message || 'Registration failed')
    }
  }

  if (success) {
    return (
      <div className="page-container">
        <div className="page-header">
          <h1 className="page-title">Account Created! ✅</h1>
          <p className="page-subtitle">Redirecting to sign in...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Create Account</h1>
        <p className="page-subtitle">Join MovieMatch to manage your groups</p>
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
              minLength={8}
              required 
            />
            <small style={{ color: '#888', fontSize: '0.875rem' }}>
              Minimum 8 characters
            </small>
          </div>
          
          <div className="form-group">
            <label className="form-label">Confirm Password</label>
            <input 
              className="form-input"
              value={confirmPassword} 
              onChange={e => setConfirmPassword(e.target.value)} 
              type="password" 
              placeholder="••••••••"
              required 
            />
          </div>
          
          <button type="submit" className="btn btn-primary btn-large">
            Create Account
          </button>
          
          <div style={{ marginTop: '1rem', textAlign: 'center' }}>
            <span style={{ color: '#888' }}>Already have an account? </span>
            <a href="/signin" style={{ color: '#4CAF50', textDecoration: 'none', fontWeight: 500 }}>
              Sign in
            </a>
          </div>
        </form>
        
        {error && <div role="alert" className="alert alert-error">{error}</div>}
      </div>
    </div>
  )
}
