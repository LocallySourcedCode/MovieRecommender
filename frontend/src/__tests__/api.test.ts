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

  it('createGroupGuest does not send Authorization header when token is set', async () => {
    setToken('tokz')
    const spy = vi.fn().mockResolvedValue(new Response(JSON.stringify({ group: { code: 'XYZ789' }, access_token: 'ptok2' }), { status: 200 }))
    global.fetch = spy as any
    await api.createGroupGuest('Guest')
    const init = (spy as any).mock.calls[0][1]
    expect(init.headers['Authorization']).toBeUndefined()
  })

  it('joinGroupGuest does not send Authorization header when token is set', async () => {
    setToken('tokz')
    const spy = vi.fn().mockResolvedValue(new Response(JSON.stringify({ group: { code: 'ABC123' }, access_token: 'ptok' }), { status: 200 }))
    global.fetch = spy as any
    await api.joinGroupGuest('ABC123', 'G')
    const init = (spy as any).mock.calls[0][1]
    expect(init.headers['Authorization']).toBeUndefined()
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


// Additional tests for genre API methods
import { vi as _vi } from 'vitest'

describe('api client - genres', () => {
  const origFetch = global.fetch
  beforeEach(() => {
    _vi.restoreAllMocks()
    global.fetch = _vi.fn() as any
  })
  afterEach(() => {
    global.fetch = origFetch as any
  })

  it('getGenreStandings calls the correct endpoint', async () => {
    ;(global.fetch as any).mockResolvedValueOnce(new Response(JSON.stringify({ standings: [] }), { status: 200 }))
    await api.getGenreStandings('ABC123')
    const args = (global.fetch as any).mock.calls[0]
    expect(args[0]).toBe(`${API_BASE}/groups/ABC123/genres/standings`)
  })

  it('resetGenres posts to the reset endpoint', async () => {
    ;(global.fetch as any).mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200 }))
    await api.resetGenres('ABC123')
    const args = (global.fetch as any).mock.calls[0]
    expect(args[0]).toBe(`${API_BASE}/groups/ABC123/genres/reset`)
    expect(args[1].method).toBe('POST')
  })
})
