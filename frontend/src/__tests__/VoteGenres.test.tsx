import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { VoteGenres } from '../pages/VoteGenres'

vi.mock('../api', () => ({
  api: {
    getGenreStandings: vi.fn().mockResolvedValue({
      standings: [ { genre: 'Action', votes: 2 }, { genre: 'Comedy', votes: 1 } ],
      leader: 'Action',
      nominations: [ { genre: 'Action', count: 2 }, { genre: 'Comedy', count: 1 } ]
    }),
    voteGenre: vi.fn().mockResolvedValue({ ok: true }),
    getProgress: vi.fn().mockResolvedValue({ phase: 'genre_voting' })
  }
}))

import { api } from '../api'

describe('VoteGenres page', () => {
  it('shows standings and allows voting on a genre', async () => {
    render(
      <MemoryRouter initialEntries={["/g/ABC123/vote-genres"]}>
        <Routes>
          <Route path="/g/:code/vote-genres" element={<VoteGenres />} />
        </Routes>
      </MemoryRouter>
    )

    // Wait for standings to render and assert content instead of brittle header text
    const actionRows = await screen.findAllByText(/Action: 2/i)
    expect(actionRows.length).toBeGreaterThan(0)

    const voteBtn = (await screen.findAllByText('Vote'))[0]
    fireEvent.click(voteBtn)

    const msg = await screen.findByText(/Voted for/i)
    expect(msg).toBeInTheDocument()
  })

  it('allows voting from nominations list when standings are empty', async () => {
    ;(api.getGenreStandings as any).mockResolvedValueOnce({ standings: [], leader: null, nominations: [ { genre: 'Drama', count: 1 } ] })
    render(
      <MemoryRouter initialEntries={["/g/ABC123/vote-genres"]}>
        <Routes>
          <Route path="/g/:code/vote-genres" element={<VoteGenres />} />
        </Routes>
      </MemoryRouter>
    )
    const voteBtns = await screen.findAllByText('Vote')
    expect(voteBtns.length).toBeGreaterThan(0)
    fireEvent.click(voteBtns[0])
    const msg = await screen.findByText(/Voted for/i)
    expect(msg).toBeInTheDocument()
  })
})
