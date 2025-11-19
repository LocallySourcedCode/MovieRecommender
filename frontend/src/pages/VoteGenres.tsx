import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'

export function VoteGenres() {
  const { code } = useParams()
  const nav = useNavigate()
  const [standings, setStandings] = useState<{ genre: string; votes: number }[]>([])
  const [noms, setNoms] = useState<{ genre: string; count: number }[]>([])
  const [leader, setLeader] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [isHost, setIsHost] = useState(false)

  if (!code) return <div>Missing group code</div>

  async function refresh() {
    try {
      const data = await api.getGenreStandings(code!)
      setStandings(data?.standings || [])
      setLeader(data?.leader || null)
      setNoms(data?.nominations || [])
    } catch (err: any) {
      setError(err?.message || 'Failed to load standings')
    }
  }

  useEffect(() => {
    refresh()
    const anyApi: any = api as any
    if (typeof anyApi.whoami === 'function') {
      anyApi.whoami().then((w: any) => {
        const host = Boolean(w?.is_host)
        setIsHost(host)
      }).catch(() => setIsHost(false))
    } else {
      setIsHost(false)
    }
    let active = true
    async function poll() {
      try {
        const p = await api.getProgress(code!)
        if (!active) return
        if (p.phase === 'movie_selection') {
          nav(`/g/${code}/movies`)
        }
        // When finalized, stay on this page to show genre voting results
      } catch {}
      if (active) setTimeout(poll, 3000)
    }
    poll()
    return () => { active = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code])

  function friendlyError(msg: string): string {
    if (!msg) return 'Vote failed'
    if (msg.includes('Vote limit reached')) return 'You\'ve used all 3 of your votes.'
    if (msg.includes('Genre not nominated')) return 'That genre is not currently nominated.'
    return msg
  }

  async function vote(g: string) {
    setError(null)
    setMessage(null)
    try {
      await api.voteGenre(code!, g)
      setMessage(`Voted for ${g}`)
      await refresh()
    } catch (err: any) {
      setError(friendlyError(err?.message))
    }
  }

  return (
    <div className="page-container-wide">
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '2rem' }}>
        <button onClick={() => nav(`/g/${code}`)} className="btn btn-back">
          ← Back
        </button>
        <h1 style={{ flex: 1, textAlign: 'center', fontSize: '2rem', fontWeight: 700, color: 'white', margin: 0 }}>Vote for Genres</h1>
        <span style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.95rem' }}>Group: {code}</span>
      </div>
      
      {leader && (
        <div className="leader-banner">
          <span className="leader-text">🏆 Leading Genre: {leader}</span>
        </div>
      )}
      
      <div className="standings-container">
        <div className="card">
          <h3 className="card-title">📊 Standings</h3>
          {standings.length === 0 ? (
            <p style={{ color: '#6b7280' }}>No votes yet</p>
          ) : (
            <ul className="standings-list">
              {standings.map((row, idx) => (
                <li key={row.genre} className="standings-item">
                  <span className="standings-rank">#{idx + 1}</span>
                  <span className="standings-genre">{row.genre}</span>
                  <span className="standings-votes">{row.votes} votes</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        
        <div className="card">
          <h3 className="card-title">✨ Nominated Genres</h3>
          <p style={{ color: '#6b7280', marginBottom: '1rem', fontSize: '0.95rem' }}>You have 3 votes to distribute</p>
          {noms.length === 0 ? (
            <p style={{ color: '#6b7280' }}>No nominations yet</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {noms.map(row => (
                <div key={row.genre} className="vote-item">
                  <span className="vote-genre">{row.genre}</span>
                  <span className="vote-count">({row.count} nominations)</span>
                  <button onClick={() => vote(row.genre)} className="btn btn-primary" style={{ padding: '0.5rem 1rem' }}>
                    🗳️ Vote
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      <div className="card" style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <button 
          onClick={() => nav(`/g/${code}/movies`)}
          className="btn btn-primary"
          style={{ flex: 1, minWidth: '200px' }}
        >
          🎬 Go to Movie Selection
        </button>
        {isHost && (
          <button 
            title="Restart movie recommendation process to genre nomination" 
            onClick={async ()=>{ try { await api.resetGenres(code!); nav(`/g/${code}/nominate-genres`) } catch(e){} }}
            className="btn btn-danger"
            style={{ flex: 1, minWidth: '200px' }}
          >
            🔄 Restart
          </button>
        )}
      </div>
      
      {message && <div className="alert alert-success">{message}</div>}
      {error && <div role="alert" className="alert alert-error">{error}</div>}
    </div>
  )
}
