import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { api } from '../api'
import { setToken, clearToken, getToken } from '../utils/storage'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

describe('api client', () => {
  const origFetch = global.fetch

  beforeEach(() => {
    vi.restoreAllMocks()
    clearToken()
    global.fetch = vi.fn() as any
  })
  afterEach(() => {
    global.fetch = origFetch as any
  })

  it('login stores token', async () => {
    ;(global.fetch as any)
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: 'abc', token_type: 'bearer' }), { status: 200 }))
    const res = await api.login('user@example.com', 'secret')
    expect(res.access_token).toBe('abc')
    expect(getToken()).toBe('abc')
  })

  it('createGroupGuest stores token and returns group', async () => {
    ;(global.fetch as any)
      .mockResolvedValueOnce(new Response(JSON.stringify({ group: { code: 'ABC123' }, access_token: 'ptok' }), { status: 200 }))
    const res = await api.createGroupGuest('Guest')
    expect(res.group.code).toBe('ABC123')
    expect(getToken()).toBe('ptok')
  })

  it('currentMovie uses Authorization header when token present', async () => {
    setToken('tok1')
    const spy = vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'current', candidate: { id: 1, title: 'Inception' } }), { status: 200 }))
    global.fetch = spy as any
    await api.currentMovie('ABC123')
    const url = `${API_BASE}/groups/ABC123/movies/current`
    expect(spy).toHaveBeenCalled()
    const args = (spy as any).mock.calls[0]
    expect(args[0]).toBe(url)
    const init = args[1]
    expect(init.headers['Authorization']).toBe('Bearer tok1')
  })
})
