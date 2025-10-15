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
    <div style={{ maxWidth: 420 }}>
      <h3>Sign In</h3>
      <form onSubmit={onSubmit}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <label>
            Email
            <input value={email} onChange={e => setEmail(e.target.value)} type="email" placeholder="you@example.com" required />
          </label>
          <label>
            Password
            <input value={password} onChange={e => setPassword(e.target.value)} type="password" required />
          </label>
          <button type="submit">Sign In</button>
        </div>
      </form>
      {error && <div role="alert" style={{ color: 'crimson', marginTop: 8 }}>{error}</div>}
    </div>
  )
}
