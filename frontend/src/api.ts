import { getToken, setToken } from './utils/storage'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

async function request(path: string, opts: RequestInit = {}) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers: { ...headers, ...(opts.headers || {}) } })
  if (!res.ok) {
    const msg = await safeText(res)
    throw new Error(`${res.status} ${msg}`)
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
    const data = await request('/groups', { method: 'POST', body: JSON.stringify({ display_name, streaming_services }) })
    if (data?.access_token) setToken(data.access_token)
    return data
  },
  async createGroupAsUser() {
    return request('/groups', { method: 'POST' })
  },
  async joinGroupGuest(code: string, display_name: string, streaming_services?: string[]) {
    const data = await request(`/groups/${code}/join`, { method: 'POST', body: JSON.stringify({ display_name, streaming_services }) })
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
}
