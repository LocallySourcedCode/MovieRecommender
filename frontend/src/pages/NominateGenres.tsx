import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { GenreToggle } from '../components/GenreToggle'

export function NominateGenres() {
  const { code } = useParams()
  const nav = useNavigate()
  const [selected, setSelected] = useState<string[]>([])
  const [tally, setTally] = useState<{ genre: string; count: number }[]>([])
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [progress, setProgress] = useState<{ nominated_count: number; total_participants: number; phase: string } | null>(null)
  const [isHost, setIsHost] = useState(false)

  if (!code) return <div>Missing group code</div>

  async function refresh() {
    try {
      const data = await api.getGenreNominations(code)
      setTally(data?.nominations || [])
    } catch (err: any) {
      setError(err?.message || 'Failed to load nominations')
    }
  }

  async function fetchProgress() {
    try {
      const p = await api.getProgress(code!)
      setProgress({ nominated_count: p.nominated_count, total_participants: p.total_participants, phase: p.phase })
      if (p.phase === 'genre_voting') nav(`/g/${code}/vote-genres`)
    } catch {}
  }

  useEffect(() => {
    refresh()
    fetchProgress()
    const anyApi: any = api as any
    if (typeof anyApi.whoami === 'function') {
      anyApi.whoami().then((w: any) => {
        const host = Boolean(w?.is_host)
        setIsHost(host)
      }).catch(() => setIsHost(false))
    } else {
      setIsHost(false)
    }
    const t = setInterval(fetchProgress, 3000)
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code])

  function friendlyError(msg: string): string {
    if (!msg) return 'Something went wrong while submitting your nomination.'
    if (msg.includes('Nomination limit') || msg.includes('exceed')) {
      return 'You\'ve reached the maximum of 2 nominations. You can adjust your picks or wait for the next round.'
    }
    if (msg.includes('At least one')) {
      return 'Please select at least one genre.'
    }
    return msg
  }

  async function submit() {
    setError(null)
    setSaving(true)
    try {
      if (selected.length === 0) {
        setError('Please select at least one genre.')
        setSaving(false)
        return
      }
      await api.nominateGenres(code, selected)
      await refresh()
      // After nominate, suggest going to vote screen
      nav(`/g/${code}/vote-genres`)
    } catch (err: any) {
      setError(friendlyError(err?.message))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page-container-wide">
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '2rem' }}>
        <button onClick={() => nav(`/g/${code}`)} className="btn btn-back">
          ← Back
        </button>
        <h1 style={{ flex: 1, textAlign: 'center', fontSize: '2rem', fontWeight: 700, color: 'white', margin: 0 }}>Nominate Genres</h1>
        {progress && (
          <div className="badge badge-host">
            ✅ {progress.nominated_count} / {progress.total_participants} Nominated
          </div>
        )}
      </div>
      
      <div className="card">
        <h2 className="card-title">Select Your Favorite Genres</h2>
        <GenreToggle value={selected} onChange={setSelected} />
        
        <div className="btn-group">
          <button onClick={submit} disabled={saving || selected.length === 0} className="btn btn-primary">
            ✨ Submit Nomination
          </button>
          {isHost && (
            <button 
              title="Restart movie recommendation process to genre nomination" 
              type="button" 
              onClick={async ()=>{ try { await api.resetGenres(code!); nav(`/g/${code}/nominate-genres`) } catch(e){} }}
              className="btn btn-danger"
            >
              🔄 Restart
            </button>
          )}
        </div>
        
        {error && <div role="alert" className="alert alert-error">{error}</div>}
      </div>
      
      <div className="card">
        <h3 className="card-title">Current Nominations</h3>
        {tally.length === 0 ? (
          <p style={{ color: '#6b7280' }}>No nominations yet. Be the first!</p>
        ) : (
          <div className="pill-group">
            {tally.map(row => (
              <div key={row.genre} className="pill active" style={{ cursor: 'default' }}>
                {row.genre} <span style={{ marginLeft: '0.5rem', background: 'rgba(255,255,255,0.3)', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>{row.count}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
