import { describe, it, expect, afterEach } from 'vitest'
import { getApiBaseUrl } from '../client'

describe('getApiBaseUrl', () => {
  const originalEnv = import.meta.env.VITE_API_URL

  afterEach(() => {
    import.meta.env.VITE_API_URL = originalEnv
  })

  it('returns /api/v1 when no environment variable is provided', () => {
    import.meta.env.VITE_API_URL = ''
    expect(getApiBaseUrl()).toBe('/api/v1')
  })

  it('appends /api/v1 when given a bare domain without trailing slash', () => {
    import.meta.env.VITE_API_URL = 'https://kirubai-backend.onrender.com'
    expect(getApiBaseUrl()).toBe('https://kirubai-backend.onrender.com/api/v1')
  })

  it('appends /api/v1 when given a bare domain with trailing slash', () => {
    import.meta.env.VITE_API_URL = 'https://kirubai-backend.onrender.com/'
    expect(getApiBaseUrl()).toBe('https://kirubai-backend.onrender.com/api/v1')
  })

  it('preserves existing /api/v1 without duplicating', () => {
    import.meta.env.VITE_API_URL = 'https://kirubai-backend.onrender.com/api/v1'
    expect(getApiBaseUrl()).toBe('https://kirubai-backend.onrender.com/api/v1')
  })

  it('trims trailing slash from existing /api/v1/', () => {
    import.meta.env.VITE_API_URL = 'https://kirubai-backend.onrender.com/api/v1/'
    expect(getApiBaseUrl()).toBe('https://kirubai-backend.onrender.com/api/v1')
  })
})
