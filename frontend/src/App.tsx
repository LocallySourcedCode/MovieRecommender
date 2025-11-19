import React, { useEffect, useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { api } from './api'
import { getToken, clearToken } from './utils/storage'

export function App() {
  const [who, setWho] = useState<{ kind: string; email?: string; display_name?: string; group_id?: number } | null>(null)
  const [groupCode, setGroupCode] = useState<string | null>(null)
  const nav = useNavigate()
  const location = useLocation()

  useEffect(() => {
    let mounted = true
    if (getToken()) {
      api.whoami().then(w => {
        if (mounted) setWho(w)
      }).catch(() => setWho(null))
    } else {
      setWho(null)
    }
    
    // Extract group code from URL if present
    const match = location.pathname.match(/\/g\/([A-Z0-9]+)/)
    if (match) {
      setGroupCode(match[1])
    } else {
      setGroupCode(null)
    }
    
    return () => { mounted = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname])

  function logout() {
    clearToken()
    setWho(null)
    nav('/signin')
  }

  return (
    <div>
      <header className="app-header">
        <Link to="/" className="app-logo">
          <div className="app-logo-icon">🎬</div>
          <span>MovieMatch</span>
        </Link>
        <nav className="app-nav">
          <Link to="/groups/new" className="nav-link">New Group</Link>
          <Link to="/join" className="nav-link">Join Group</Link>
          {groupCode && (
            <Link to={`/g/${groupCode}`} className="nav-link">Our Group</Link>
          )}
          <Link to="/signin" className="nav-link">Sign In</Link>
        </nav>
        <div className="user-info">
          {who ? (
            <>
              <span className="user-badge">{who.email || who.display_name}</span>
              <button onClick={logout} className="btn btn-secondary">Log out</button>
            </>
          ) : (
            <span className="guest-badge">Guest mode</span>
          )}
        </div>
      </header>
      <div className="app-content">
        <Outlet />
      </div>
    </div>
  )
}
