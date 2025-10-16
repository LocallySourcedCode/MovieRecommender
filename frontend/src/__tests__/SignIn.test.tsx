import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { SignIn } from '../pages/SignIn'
import { api } from '../api'

vi.mock('../api', () => ({
  api: {
    login: vi.fn().mockResolvedValue({ access_token: 'tok' })
  }
}))

describe('SignIn page', () => {
  it('submits email/password and calls login API', async () => {
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
    const submit = screen.getByRole('button', { name: 'Sign In' })
    fireEvent.click(submit)

    // Assert API was called with provided credentials (navigation is handled by router and tested elsewhere)
    expect((api.login as any).mock.calls[0]).toEqual(['a@b.com', 'secret'])
  })
})
