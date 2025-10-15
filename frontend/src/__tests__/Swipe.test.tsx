import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Swipe } from '../components/Swipe'

vi.mock('../api', () => {
  const current = vi.fn().mockResolvedValue({ status: 'current', candidate: { id: 1, title: 'Inception' } })
  const vote = vi.fn().mockResolvedValue({ status: 'pending' })
  return { api: { currentMovie: current, voteMovie: vote } }
})

describe('Swipe component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads current candidate and shows title', async () => {
    render(<Swipe code="ABC123" />)
    const title = await screen.findByText(/Inception/)
    expect(title).toBeInTheDocument()
  })

  it('clicking Yes sets pending by default', async () => {
    render(<Swipe code="ABC123" />)
    await screen.findByText(/Inception/)
    fireEvent.click(screen.getByText('Yes'))
    const pending = await screen.findByText(/Waiting for others/)
    expect(pending).toBeInTheDocument()
  })
})
