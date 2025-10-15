import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { GroupLobby } from '../pages/GroupLobby'

vi.mock('../api', () => ({
  api: {
    useVeto: vi.fn().mockResolvedValue({ status: 'current', candidate: { id: 2, title: 'Parasite' } })
  }
}))

vi.mock('../components/Swipe', () => ({
  Swipe: ({ code }: { code: string }) => <div>SWIPE AREA {code}</div>
}))

describe('GroupLobby page', () => {
  it('renders with code and can call veto', async () => {
    render(
      <MemoryRouter initialEntries={["/g/ABC123"]}>
        <Routes>
          <Route path="/g/:code" element={<GroupLobby />} />
        </Routes>
      </MemoryRouter>
    )
    expect(screen.getByText('Group Lobby (ABC123)')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Use Veto'))
    const msg = await screen.findByText(/vetoed/i)
    expect(msg).toBeInTheDocument()
  })
})
