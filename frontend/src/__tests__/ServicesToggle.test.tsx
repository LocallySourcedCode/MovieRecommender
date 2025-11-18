import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import React, { useState } from 'react'
import { ServicesToggle } from '../components/ServicesToggle'

function Wrapper() {
  const [val, setVal] = useState<string[]>([])
  return <ServicesToggle value={val} onChange={setVal} />
}

describe('ServicesToggle', () => {
  it('toggles selections and reflects aria-pressed', async () => {
    render(<Wrapper />)

    const netflixBtn = screen.getByRole('button', { name: 'Netflix' })
    const huluBtn = screen.getByRole('button', { name: 'Hulu' })

    expect(netflixBtn).toHaveAttribute('aria-pressed', 'false')
    fireEvent.click(netflixBtn)
    expect(netflixBtn).toHaveAttribute('aria-pressed', 'true')

    fireEvent.click(huluBtn)
    expect(huluBtn).toHaveAttribute('aria-pressed', 'true')

    // Toggling off
    fireEvent.click(netflixBtn)
    expect(netflixBtn).toHaveAttribute('aria-pressed', 'false')
  })
})
