import '@testing-library/jest-dom/vitest'
import { afterEach, beforeAll, afterAll } from 'vitest'
import { cleanup } from '@testing-library/react'

// Filter non-actionable React Router future notices in tests to keep output clean
let originalWarn: typeof console.warn
beforeAll(() => {
  originalWarn = console.warn
  console.warn = (...args: any[]) => {
    const msg = String(args[0] ?? '')
    if (/React Router( v?7)?( future)?/i.test(msg) || /You can silence these warnings by/i.test(msg)) {
      return
    }
    originalWarn(...args)
  }
})

afterAll(() => {
  console.warn = originalWarn
})

// Run cleanup after each test case (RTL)
afterEach(() => {
  cleanup()
})
