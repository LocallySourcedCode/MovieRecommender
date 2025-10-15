import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { SignIn } from '../pages/SignIn'

vi.mock('../api', () => ({
  api: {
    login: vi.fn().mockResolvedValue({ access_token: 'tok' })
  }
}))

describe('SignIn page', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('submits email/password and navigates', async () => {
    render(
      <MemoryRouter initialEntries={['/signin']}>
        <Routes>
          <Route path="/signin" element={<SignIn />} />
          <Route path="/groups/new" element={<div>NEW GROUP</div>} />
        </Routes>
      </MemoryRouter>
    )

    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'secret' } })
    fireEvent.click(screen.getByText('Sign In'))

    const done = await screen.findByText('NEW GROUP')
    expect(done).toBeInTheDocument()
  })
})
