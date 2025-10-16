import React, { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { api } from '../api'

export function GroupLobby() {
  const { code } = useParams()
  const nav = useNavigate()
  const [msg, setMsg] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!code) return <div>Missing group code</div>

  useEffect(() => {
    let active = true
    async function go() {
      try {
        const p = await api.getProgress(code!)
        if (!active) return
        if (p.phase === 'genre_nomination' || p.phase === 'setup') nav(`/g/${code}/nominate-genres`)
        else if (p.phase === 'genre_voting') nav(`/g/${code}/vote-genres`)
        else if (p.phase === 'movie_selection' || p.phase === 'finalized') nav(`/g/${code}/movies`)
      } catch (err) {
        // ignore and show hub
      }
    }
    go()
    return () => { active = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code])

  async function resetGenres() {
    setMsg(null)
    setError(null)
    try {
      await api.resetGenres(code)
      setMsg('Genres reset. Please nominate again.')
      nav(`/g/${code}/nominate-genres`)
    } catch (err: any) {
      setError(err?.message || 'Reset failed (host only)')
    }
  }

  return (
    <div>
      <h3>Group Lobby ({code})</h3>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
        <Link to={`/g/${code}/nominate-genres`}>Nominate Genres</Link>
        <Link to={`/g/${code}/vote-genres`}>Vote Genres</Link>
        <Link to={`/g/${code}/movies`}>Movie Voting</Link>
        <button title="Restart movie recommendation process to genre nomination" onClick={resetGenres}>Restart</button>
      </div>
      {msg && <div style={{ marginTop: 8 }}>{msg}</div>}
      {error && <div role="alert" style={{ color: 'crimson', marginTop: 8 }}>{error}</div>}
    </div>
  )
}
