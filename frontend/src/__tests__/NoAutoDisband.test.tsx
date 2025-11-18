import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import React from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render } from '@testing-library/react'

vi.mock('../api', () => {
  return {
    api: {
      whoami: vi.fn().mockResolvedValue({ is_host: true }),
      getGenreNominations: vi.fn().mockResolvedValue({ nominations: [] }),
      getProgress: vi.fn().mockResolvedValue({ nominated_count: 0, total_participants: 1, phase: 'genre_nomination' }),
      getGenreStandings: vi.fn().mockResolvedValue({ standings: [], nominations: [], leader: null }),
    }
  }
})

import { Movies } from '../pages/Movies'
import { NominateGenres } from '../pages/NominateGenres'
import { VoteGenres } from '../pages/VoteGenres'

function renderWithRoute(path: string, element: React.ReactNode) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/g/:code/movies" element={element as any} />
        <Route path="/g/:code/nominate-genres" element={element as any} />
        <Route path="/g/:code/vote-genres" element={element as any} />
      </Routes>
    </MemoryRouter>
  )
}

describe('No auto-disband on beforeunload', () => {
  const addSpy = vi.spyOn(window, 'addEventListener')
  const removeSpy = vi.spyOn(window, 'removeEventListener')

  beforeEach(() => {
    addSpy.mockClear()
    removeSpy.mockClear()
  })

  afterEach(() => {
    // nothing
  })

  it('Movies page does not attach beforeunload handler', async () => {
    renderWithRoute('/g/ABC/movies', <Movies />)
    // Allow effects to run
    await Promise.resolve()
    const calls = addSpy.mock.calls.map(c => c[0])
    expect(calls.includes('beforeunload')).toBe(false)
  })

  it('NominateGenres page does not attach beforeunload handler', async () => {
    renderWithRoute('/g/ABC/nominate-genres', <NominateGenres />)
    await Promise.resolve()
    const calls = addSpy.mock.calls.map(c => c[0])
    expect(calls.includes('beforeunload')).toBe(false)
  })

  it('VoteGenres page does not attach beforeunload handler', async () => {
    renderWithRoute('/g/ABC/vote-genres', <VoteGenres />)
    await Promise.resolve()
    const calls = addSpy.mock.calls.map(c => c[0])
    expect(calls.includes('beforeunload')).toBe(false)
  })
})
