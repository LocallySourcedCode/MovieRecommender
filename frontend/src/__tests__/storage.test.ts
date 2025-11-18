import { describe, it, expect } from 'vitest'
import { getToken, setToken, clearToken } from '../utils/storage'

// JSDOM provides localStorage

describe('storage utils', () => {
  it('sets, gets, and clears token', () => {
    clearToken()
    expect(getToken()).toBeNull()
    setToken('abc')
    expect(getToken()).toBe('abc')
    clearToken()
    expect(getToken()).toBeNull()
  })
})
