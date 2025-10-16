import React, { useEffect, useState } from 'react'
import { api } from '../api'

type Candidate = { id: number; title: string; poster_url?: string; year?: number; description?: string }

type Status = 'idle' | 'current' | 'pending' | 'finalized'

export function Swipe({ code }: { code: string }) {
  const [cand, setCand] = useState<Candidate | null>(null)
  const [status, setStatus] = useState<Status>('idle')
  const [message, setMessage] = useState<string | null>(null)
  const [imgOk, setImgOk] = useState<boolean>(true)

  async function refresh() {
    const data = await api.currentMovie(code)
    setCand(data?.candidate || null)
    setStatus(data?.status || 'current')
    setImgOk(true)
  }

  useEffect(() => {
    refresh().catch(err => setMessage(err?.message || 'Failed to load current movie'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code])

  async function vote(accept: boolean) {
    setMessage(null)
    try {
      const res = await api.voteMovie(code, accept)
      if (res.status === 'finalized') {
        setStatus('finalized')
        setCand(res.winner)
      } else if (res.status === 'current') {
        // majority reject -> new current provided
        setStatus('current')
        setCand(res.candidate)
      } else {
        setStatus('pending')
      }
    } catch (err: any) {
      setMessage(err?.message || 'Vote failed')
    }
  }

  if (!cand) {
    return (
      <div>
        {message ? (
          <div>
            <div role="alert" style={{ color: 'crimson', marginBottom: 8 }}>{message}</div>
            <button onClick={() => { setMessage(null); refresh().catch(err => setMessage(err?.message || 'Failed to load current movie')) }}>Retry</button>
          </div>
        ) : (
          <div>Loading…</div>
        )}
      </div>
    )
  }
  return (
    <div style={{ display: 'flex', gap: 16 }}>
      <div>
        <h4>{cand.title} {cand.year ? `(${cand.year})` : ''}</h4>
        {cand.poster_url && imgOk && (
                  <img src={cand.poster_url} alt={cand.title} style={{ maxWidth: 240, borderRadius: 6 }} onError={() => setImgOk(false)} />
                )}
        <p style={{ maxWidth: 480 }}>{cand.description}</p>
        {status === 'finalized' ? (
          <div>Winner selected! 🎉</div>
        ) : (
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => vote(true)}>Yes</button>
            <button onClick={() => vote(false)}>No</button>
          </div>
        )}
        {status === 'pending' && <div style={{ marginTop: 8 }}>Waiting for others…</div>}
        {message && <div role="alert" style={{ color: 'crimson', marginTop: 8 }}>{message}</div>}
      </div>
    </div>
  )
}
