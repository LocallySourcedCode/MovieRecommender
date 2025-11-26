import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'

export function GroupLobby() {
  const { code } = useParams()
  const nav = useNavigate()
  const [msg, setMsg] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [who, setWho] = useState<any>(null)
  const [progress, setProgress] = useState<any>(null)

  if (!code) return <div className="loading">Missing group code</div>

  useEffect(() => {
    let active = true
    async function go() {
      try {
        const w = await api.whoami()
        if (active) setWho(w)
      } catch {}
      try {
        const p = await api.getProgress(code!)
        if (active) setProgress(p)
      } catch (err) {
        // ignore and show hub
      }
    }
    go()
    const interval = setInterval(go, 3000)
    return () => { active = false; clearInterval(interval) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code])

  async function resetGenres() {
    setMsg(null)
    setError(null)
    try {
      await api.resetGenres(code!)
      setMsg('Genres reset. Please nominate again.')
      nav(`/g/${code}/nominate-genres`)
    } catch (err: any) {
      setError(err?.message || 'Reset failed (host only)')
    }
  }

  async function leaveGroup() {
    const ok = window.confirm('Are you sure you want to leave this group?')
    if (!ok) return
    try {
      await api.leaveCurrent()
      nav('/groups/new')
    } catch (err: any) {
      setError(err?.message || 'Failed to leave group')
    }
  }

  function copyShareLink() {
    const url = `${window.location.origin}/g/${code}`
    navigator.clipboard.writeText(url).then(() => {
      setMsg('Share link copied to clipboard!')
      setTimeout(() => setMsg(null), 3000)
    }).catch(() => {
      setMsg('Failed to copy link')
    })
  }

  function getPhaseDisplay(phase: string) {
    if (phase === 'genre_nomination' || phase === 'setup') return { name: 'Genre Nomination', icon: '🎭', color: '#dbeafe' }
    if (phase === 'genre_voting') return { name: 'Genre Voting', icon: '🗳️', color: '#fef3c7' }
    if (phase === 'movie_selection') return { name: 'Movie Selection', icon: '🎬', color: '#fce7f3' }
    if (phase === 'finalized') return { name: 'Finalized', icon: '🎉', color: '#d1fae5' }
    return { name: phase, icon: '❓', color: '#f3f4f6' }
  }

  const phaseInfo = progress ? getPhaseDisplay(progress.phase) : null

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <h1 className="page-title">Our Group</h1>
        <p className="page-subtitle">Manage and view your group's movie selection journey</p>
      </div>
      
      <div className="group-code-display">
        <div className="group-code-label">Group Code</div>
        <div className="group-code-value">{code} 📋</div>
        <button onClick={copyShareLink} className="copy-link">
          Copy Share Link 🔗
        </button>
      </div>
      
      <div className="card">
        <h3 className="card-title">Your Info</h3>
        <div className="info-row">
          <span className="info-label">Display Name:</span>
          <span className="info-value">{who?.email || who?.display_name || 'Guest'}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Role:</span>
          <span className="badge badge-host">{who?.is_host ? '👑 Host' : 'Member'}</span>
        </div>
      </div>
      
      {phaseInfo && (
        <div className="card">
          <h3 className="card-title">Current Phase</h3>
          <div className="phase-status" style={{ background: phaseInfo.color }}>
            <span className="phase-icon">{phaseInfo.icon}</span>
            <div className="phase-info">
              <div className="phase-name">{phaseInfo.name}</div>
              <div className="phase-description">
                {progress.total_participants} / {progress.total_participants} participants active
              </div>
            </div>
            <div className="phase-indicator"></div>
          </div>
          
          {progress.phase === 'finalized' && (
            <button onClick={() => nav(`/g/${code}/movies`)} className="btn btn-success btn-large">
              Go to Finalized →
            </button>
          )}
          {(progress.phase === 'movie_selection') && (
            <button onClick={() => nav(`/g/${code}/movies`)} className="btn btn-primary btn-large">
              Go to Movie Voting →
            </button>
          )}
          {(progress.phase === 'genre_nomination' || progress.phase === 'setup') && (
            <button onClick={() => nav(`/g/${code}/nominate-genres`)} className="btn btn-primary btn-large">
              Go to Genre Nomination →
            </button>
          )}
          {progress.phase === 'genre_voting' && (
            <button onClick={() => nav(`/g/${code}/vote-genres`)} className="btn btn-primary btn-large">
              Go to Genre Voting →
            </button>
          )}
        </div>
      )}
      
      {progress?.finalized_genres && progress.finalized_genres.length > 0 && (
        <div style={{ background: '#f3f4f6', borderRadius: '16px', padding: '1.5rem', marginTop: '1.5rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1rem', color: '#111827', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            🎭 Winning Genres
          </h3>
          <div style={{ background: 'white', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
            {progress.finalized_genres.map((genre: string, idx: number) => (
              <div 
                key={genre}
                style={{
                  background: idx === 0 ? 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)' : 'linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)',
                  border: idx === 0 ? '2px solid #f59e0b' : '2px solid #818cf8',
                  borderRadius: '10px',
                  padding: '0.75rem 1.25rem',
                  fontSize: '1rem',
                  fontWeight: 600,
                  color: idx === 0 ? '#92400e' : '#3730a3',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                {idx === 0 && <span style={{ fontSize: '1.25rem' }}>🏆</span>}
                {idx === 1 && <span style={{ fontSize: '1.25rem' }}>🥈</span>}
                {idx > 1 && <span style={{ fontSize: '1.25rem' }}>✨</span>}
                {genre}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {progress?.winner_movie && (
        <div style={{ background: '#f3f4f6', borderRadius: '16px', padding: '1.5rem', marginTop: '1.5rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1rem', color: '#111827', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            🎉 Selected Movie
          </h3>
          <div style={{ background: 'white', borderRadius: '16px', padding: '1.5rem', display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
            {progress.winner_movie.poster_url && (
              <div style={{ flex: '0 0 auto' }}>
                <img 
                  src={progress.winner_movie.poster_url} 
                  alt={progress.winner_movie.title} 
                  style={{ 
                    width: '180px', 
                    height: 'auto',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                  }} 
                />
              </div>
            )}
            <div style={{ flex: '1 1 300px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                <span style={{ fontSize: '2rem', lineHeight: 1 }}>🏆</span>
                <div>
                  <h2 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0, lineHeight: 1.2, color: '#111827' }}>
                    {progress.winner_movie.title}
                  </h2>
                  {progress.winner_movie.year && (
                    <div style={{ fontSize: '1rem', color: '#6b7280', marginTop: '0.25rem' }}>
                      {progress.winner_movie.year}
                    </div>
                  )}
                </div>
              </div>
              <p style={{ color: '#4b5563', lineHeight: 1.6, fontSize: '0.9rem', margin: 0 }}>
                {progress.winner_movie.description}
              </p>
              <div style={{ 
                background: 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)', 
                borderRadius: '10px', 
                padding: '1rem',
                border: '2px solid #10b981',
                marginTop: '0.25rem'
              }}>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#065f46', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  🎉 Winner Selected!
                </div>
                <div style={{ fontSize: '0.9rem', color: '#047857' }}>
                  This is your group's movie choice
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      <div className="card" style={{ marginTop: '2rem' }}>
        <h3 className="card-title">Quick Actions</h3>
        <div className="btn-group" style={{ flexDirection: 'column' }}>
          <button onClick={() => nav(`/g/${code}/nominate-genres`)} className="btn btn-secondary">
            🎭 Nominate Genres
          </button>
          <button onClick={() => nav(`/g/${code}/vote-genres`)} className="btn btn-secondary">
            🗳️ Vote Genres
          </button>
          <button onClick={() => nav(`/g/${code}/movies`)} className="btn btn-secondary">
            🎬 Movie Voting
          </button>
        </div>
      </div>
      
      <div className="card" style={{ 
        background: 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)', 
        border: '2px solid #fca5a5',
        padding: '1.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '2rem',
        flexWrap: 'wrap'
      }}>
        <div style={{ flex: '1 1 300px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '1.25rem' }}>⚠️</span>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#991b1b', margin: 0 }}>Leave Group</h3>
          </div>
          <p style={{ color: '#7f1d1d', margin: 0, fontSize: '0.9rem', lineHeight: 1.5 }}>
            Exit this group session. If you're the host, the entire group will be disbanded.
          </p>
        </div>
        <button 
          onClick={leaveGroup} 
          className="btn btn-danger"
          style={{ 
            background: '#dc2626',
            padding: '0.75rem 1.5rem',
            fontSize: '1rem',
            fontWeight: 600,
            boxShadow: '0 2px 8px rgba(220, 38, 38, 0.3)',
            whiteSpace: 'nowrap',
            flex: '0 0 auto'
          }}
        >
          🚪 Leave Group
        </button>
      </div>
      
      {msg && <div className="alert alert-success">{msg}</div>}
      {error && <div role="alert" className="alert alert-error">{error}</div>}
    </div>
  )
}
