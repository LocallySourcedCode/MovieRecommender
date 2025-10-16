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
    <div>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <h3 style={{ marginRight: 'auto' }}>Nominate Genres ({code})</h3>
        {progress && (
          <div style={{ fontSize: 14, color: '#374151' }} title="Participants who have submitted nominations">
            Nominated: <strong>{progress.nominated_count}</strong> / {progress.total_participants}
          </div>
        )}
      </div>
      <GenreToggle value={selected} onChange={setSelected} />
      <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
        <button onClick={submit} disabled={saving || selected.length === 0}>Submit Nomination</button>
        {isHost && (
          <button title="Restart movie recommendation process to genre nomination" type="button" onClick={async ()=>{ try { await api.resetGenres(code!); nav(`/g/${code}/nominate-genres`) } catch(e){} }}>
            Restart
          </button>
        )}
      </div>
      {error && <div role="alert" style={{ color: '#b91c1c', background: '#fee2e2', padding: '6px 10px', borderRadius: 6, marginTop: 8 }}>{error}</div>}
      <div style={{ marginTop: 16 }}>
        <h4>Current Nominations</h4>
        <ul>
          {tally.map(row => (
            <li key={row.genre}>{row.genre}: {row.count}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}
