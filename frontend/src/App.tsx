import React, { useEffect, useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { api } from './api'
import { getToken, clearToken } from './utils/storage'

export function App() {
  const [who, setWho] = useState<{ kind: string; email?: string; display_name?: string } | null>(null)
  const nav = useNavigate()
  const location = useLocation()

  useEffect(() => {
    let mounted = true
    if (getToken()) {
      api.whoami().then(setWho).catch(() => setWho(null))
    } else {
      setWho(null)
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
    <div style={{ fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif', margin: 20 }}>
      <header style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>Movie Recommender</h2>
        <nav style={{ display: 'flex', gap: 12 }}>
          <Link to="/groups/new">New Group</Link>
          <Link to="/join">Join Group</Link>
          <Link to="/signin">Sign In</Link>
        </nav>
        <div style={{ marginLeft: 'auto' }}>
          {who ? (
            <>
              <span style={{ marginRight: 8 }}>Signed in as {who.email || who.display_name}</span>
              <button onClick={logout}>Log out</button>
            </>
          ) : (
            <span>Guest mode</span>
          )}
        </div>
      </header>
      <Outlet />
    </div>
  )
}
