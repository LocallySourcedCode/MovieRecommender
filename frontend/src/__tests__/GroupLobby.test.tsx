import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { GroupLobby } from '../pages/GroupLobby'

vi.mock('../api', () => ({
  api: {
    // On load, GroupLobby queries progress and redirects based on phase
    getProgress: vi.fn().mockResolvedValue({ phase: 'genre_nomination' })
  }
}))

describe('GroupLobby page', () => {
  it('redirects to nomination page based on progress phase', async () => {
    render(
      <MemoryRouter initialEntries={["/g/ABC123"]}>
        <Routes>
          <Route path="/g/:code" element={<GroupLobby />} />
          <Route path="/g/:code/nominate-genres" element={<div>NOMINATE PAGE</div>} />
        </Routes>
      </MemoryRouter>
    )
    const el = await screen.findByText('NOMINATE PAGE')
    expect(el).toBeInTheDocument()
  })
})
