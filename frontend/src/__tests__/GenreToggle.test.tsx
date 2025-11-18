import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import React, { useState } from 'react'
import { GenreToggle } from '../components/GenreToggle'

function Wrapper() {
  const [val, setVal] = useState<string[]>([])
  return <GenreToggle value={val} onChange={setVal} />
}

describe('GenreToggle', () => {
  it('caps selections at 2 and disables others', () => {
    render(<Wrapper />)

    const actionBtn = screen.getByRole('button', { name: 'Action' })
    const comedyBtn = screen.getByRole('button', { name: 'Comedy' })
    const dramaBtn = screen.getByRole('button', { name: 'Drama' })

    // Select Action and Comedy
    expect(actionBtn).toHaveAttribute('aria-pressed', 'false')
    fireEvent.click(actionBtn)
    expect(actionBtn).toHaveAttribute('aria-pressed', 'true')

    fireEvent.click(comedyBtn)
    expect(comedyBtn).toHaveAttribute('aria-pressed', 'true')

    // Now cap reached, Drama should be disabled and not become pressed
    expect(dramaBtn).toHaveAttribute('aria-disabled', 'true')
    fireEvent.click(dramaBtn)
    expect(dramaBtn).toHaveAttribute('aria-pressed', 'false')
  })
})
