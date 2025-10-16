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
      const data = await api.getGenreStandings(code)
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
        if (p.phase === 'movie_selection' || p.phase === 'finalized') {
          nav(`/g/${code}/movies`)
        }
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
    <div>
      <h3>Vote Genres ({code})</h3>
      {leader && <div style={{ marginBottom: 8 }}>Current leader: <strong>{leader}</strong></div>}
      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
        <div>
          <h4>Standings</h4>
          <ul>
            {standings.length === 0 && <li>No votes yet</li>}
            {standings.map(row => (
              <li key={row.genre}>
                {row.genre}: {row.votes}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h4>Nominated Genres</h4>
          <ul>
            {noms.length === 0 && <li>No nominations yet</li>}
            {noms.map(row => (
              <li key={row.genre}>
                <button onClick={() => vote(row.genre)} style={{ marginRight: 8 }}>Vote</button>
                {row.genre}: {row.count}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
        {isHost && (
          <button title="Restart movie recommendation process to genre nomination" onClick={async ()=>{ try { await api.resetGenres(code!); nav(`/g/${code}/nominate-genres`) } catch(e){} }}>
            Restart
          </button>
        )}
      </div>
      {message && <div style={{ marginTop: 8 }}>{message}</div>}
      {error && <div role="alert" style={{ color: '#b91c1c', background: '#fee2e2', padding: '6px 10px', borderRadius: 6, marginTop: 8 }}>{error}</div>}
    </div>
  )
}
