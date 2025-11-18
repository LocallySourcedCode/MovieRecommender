import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { NominateGenres } from '../pages/NominateGenres'

vi.mock('../api', () => ({
  api: {
    getGenreNominations: vi.fn().mockResolvedValue({ nominations: [] }),
    nominateGenres: vi.fn().mockResolvedValue({ ok: true }),
    getProgress: vi.fn().mockResolvedValue({ nominated_count: 0, total_participants: 2, phase: 'genre_nomination' }),
    whoami: vi.fn().mockResolvedValue({ kind: 'participant', is_host: false })
  }
}))

import { api } from '../api'

describe('NominateGenres page', () => {
  it('allows selecting up to two genres and submits', async () => {
    render(
      <MemoryRouter initialEntries={["/g/ABC123/nominate-genres"]}>
        <Routes>
          <Route path="/g/:code/nominate-genres" element={<NominateGenres />} />
          <Route path="/g/:code/vote-genres" element={<div>VOTE PAGE</div>} />
        </Routes>
      </MemoryRouter>
    )

    const actionBtn = await screen.findByRole('button', { name: 'Action' })
    const comedyBtn = screen.getByRole('button', { name: 'Comedy' })
    const dramaBtn = screen.getByRole('button', { name: 'Drama' })

    fireEvent.click(actionBtn)
    fireEvent.click(comedyBtn)
    // Third should be ignored (disabled by cap)
    fireEvent.click(dramaBtn)

    fireEvent.click(screen.getByText('Submit Nomination'))

    const next = await screen.findByText('VOTE PAGE')
    expect(next).toBeInTheDocument()
  })

  it('shows friendly error when nomination limit reached', async () => {
    ;(api.nominateGenres as any).mockRejectedValueOnce(new Error('Nomination limit reached (2)'))
    render(
      <MemoryRouter initialEntries={["/g/ABC123/nominate-genres"]}>
        <Routes>
          <Route path="/g/:code/nominate-genres" element={<NominateGenres />} />
        </Routes>
      </MemoryRouter>
    )
    const actionBtn = await screen.findByRole('button', { name: 'Action' })
    const comedyBtn = screen.getByRole('button', { name: 'Comedy' })
    fireEvent.click(actionBtn)
    fireEvent.click(comedyBtn)
    fireEvent.click(screen.getByText('Submit Nomination'))
    const alert = await screen.findByRole('alert')
    expect(alert.textContent).toMatch(/maximum of 2 nominations/i)
  })
})
