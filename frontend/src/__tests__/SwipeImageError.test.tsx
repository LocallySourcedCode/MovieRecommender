import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import React from 'react'
import { Swipe } from '../components/Swipe'

vi.mock('../api', () => ({
  api: {
    currentMovie: vi.fn().mockResolvedValue({ status: 'current', candidate: { id: 1, title: 'Test', poster_url: 'http://bad/img.jpg', description: 'desc', year: 2020 } }),
    voteMovie: vi.fn(),
  }
}))

describe('Swipe component image error handling', () => {
  it('hides broken poster images on error and shows description', async () => {
    render(<Swipe code="ABC123" />)
    const title = await screen.findByText(/Test/)
    expect(title).toBeInTheDocument()
    const img = screen.getByAltText('Test') as HTMLImageElement
    // Simulate image load error
    fireEvent.error(img)
    await waitFor(() => {
      expect(screen.queryByAltText('Test')).toBeNull()
    })
    // Description should still be visible
    expect(screen.getByText('desc')).toBeInTheDocument()
  })
})
