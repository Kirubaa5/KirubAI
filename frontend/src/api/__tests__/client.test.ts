import { describe, it, expect } from 'vitest'
import { getApiBaseUrl } from '../client'

describe('getApiBaseUrl', () => {
  it('returns /api/v1 when no environment variable is provided', () => {
    expect(getApiBaseUrl()).toBe('/api/v1')
  })
})
