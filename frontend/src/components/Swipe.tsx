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
      <div className="card">
        {message ? (
          <div>
            <div role="alert" className="alert alert-error">{message}</div>
            <button onClick={() => { setMessage(null); refresh().catch(err => setMessage(err?.message || 'Failed to load current movie')) }} className="btn btn-primary">
              Retry
            </button>
          </div>
        ) : (
          <div className="loading">Loading movie…</div>
        )}
      </div>
    )
  }
  return (
    <div>
      {status === 'finalized' && (
        <div className="winner-card">
          <div className="winner-title">🎉 Winner Selected!</div>
          <div className="winner-subtitle">This is your group's movie choice</div>
        </div>
      )}
      
      <div className="movie-card">
        {cand.poster_url && imgOk && (
          <div className="movie-poster">
            <img src={cand.poster_url} alt={cand.title} onError={() => setImgOk(false)} />
          </div>
        )}
        <div className="movie-info">
          <h2 className="movie-title">
            {status === 'finalized' && '🏆 '}
            {cand.title}
            {cand.year && <span className="movie-year">{cand.year}</span>}
          </h2>
          <p className="movie-description">{cand.description}</p>
          
          {status === 'finalized' ? (
            <div className="winner-card" style={{ marginTop: '1rem' }}>
              <div className="winner-subtitle">This is your group's movie choice</div>
            </div>
          ) : (
            <>
              <div className="btn-group">
                <button onClick={() => vote(true)} className="btn btn-success btn-large">
                  👍 Yes
                </button>
                <button onClick={() => vote(false)} className="btn btn-danger btn-large">
                  👎 No
                </button>
              </div>
              {status === 'pending' && (
                <div className="alert alert-info" style={{ marginTop: '1rem' }}>
                  Waiting for other participants to vote…
                </div>
              )}
            </>
          )}
          {message && <div role="alert" className="alert alert-error" style={{ marginTop: '1rem' }}>{message}</div>}
        </div>
      </div>
    </div>
  )
}
