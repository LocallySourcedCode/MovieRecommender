import { getToken, setToken } from './utils/storage'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

type RequestOpts = RequestInit & { skipAuth?: boolean }

async function request(path: string, opts: RequestOpts = {}) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token && !opts.skipAuth) headers['Authorization'] = `Bearer ${token}`
  const { skipAuth, ...rest } = opts
  const res = await fetch(`${API_BASE}${path}`, { ...rest, headers: { ...headers, ...(opts.headers || {}) } })
  if (!res.ok) {
    // Try to parse JSON error bodies and surface a friendly message
    try {
      const data = await res.json()
      const detail = (data && data.detail) || data
      if (typeof detail === 'string') throw new Error(detail)
      if (detail && typeof detail.message === 'string') throw new Error(detail.message)
    } catch {}
    const msg = await safeText(res)
    throw new Error(msg || `${res.status} Error`)
  }
  return res.status === 204 ? null : res.json()
}

async function safeText(res: Response) {
  try { return await res.text() } catch { return '' }
}

export const api = {
  async register(email: string, password: string) {
    return request('/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) })
  },
  async login(email: string, password: string) {
    const form = new URLSearchParams({ username: email, password })
    const res = await fetch(`${API_BASE}/auth/login`, { method: 'POST', body: form })
    if (!res.ok) throw new Error(String(res.status))
    const data = await res.json()
    if (data?.access_token) setToken(data.access_token)
    return data
  },
  async whoami() {
    return request('/whoami')
  },
  async createGroupGuest(display_name: string, streaming_services?: string[]) {
    const data = await request('/groups', { method: 'POST', body: JSON.stringify({ display_name, streaming_services }), skipAuth: true })
    if (data?.access_token) setToken(data.access_token)
    return data
  },
  async createGroupAsUser() {
    return request('/groups', { method: 'POST' })
  },
  async joinGroupGuest(code: string, display_name: string, streaming_services?: string[]) {
    const data = await request(`/groups/${code}/join`, { method: 'POST', body: JSON.stringify({ display_name, streaming_services }), skipAuth: true })
    if (data?.access_token) setToken(data.access_token)
    return data
  },
  async joinGroupAsUser(code: string) {
    return request(`/groups/${code}/join`, { method: 'POST' })
  },
  async currentMovie(code: string) {
    return request(`/groups/${code}/movies/current`)
  },
  async voteMovie(code: string, accept: boolean) {
    return request(`/groups/${code}/movies/vote`, { method: 'POST', body: JSON.stringify({ accept }) })
  },
  async useVeto(code: string) {
    return request(`/groups/${code}/veto/use`, { method: 'POST' })
  },
  async leaveCurrent() {
    return request(`/groups/leave`, { method: 'POST' })
  },
  async leaveCurrentKeepAlive() {
    const token = getToken()
    if (!token) return
    try {
      await fetch(`${API_BASE}/groups/leave`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        keepalive: true,
      })
    } catch {
      // best-effort
    }
  },
  async getGenreNominations(code: string) {
    return request(`/groups/${code}/genres/nominations`)
  },
  async nominateGenres(code: string, genres: string[]) {
    return request(`/groups/${code}/genres/nominate`, { method: 'POST', body: JSON.stringify({ genres }) })
  },
  async getGenreStandings(code: string) {
    return request(`/groups/${code}/genres/standings`)
  },
  async voteGenre(code: string, genre: string) {
    return request(`/groups/${code}/genres/vote`, { method: 'POST', body: JSON.stringify({ genre }) })
  },
  async resetGenres(code: string) {
    return request(`/groups/${code}/genres/reset`, { method: 'POST' })
  },
  async getProgress(code: string) {
    return request(`/groups/${code}/progress`)
  }
}
