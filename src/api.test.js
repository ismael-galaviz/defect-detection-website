import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, errorMessage, post } from './api.js'

const FE = { network: 'N', rateLimited: 'R', invalid: 'I' }

afterEach(() => vi.unstubAllGlobals())

describe('api client', () => {
  it('posts JSON to /api and returns the body', async () => {
    const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ ok: true }) })
    vi.stubGlobal('fetch', fetch)
    expect(await post('/contact', { a: 1 })).toEqual({ ok: true })
    const [url, opts] = fetch.mock.calls[0]
    expect(url).toBe('/api/contact')
    expect(opts.method).toBe('POST')
    expect(JSON.parse(opts.body)).toEqual({ a: 1 })
  })

  it('throws ApiError with code and fields on error responses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false, status: 422, json: async () => ({ error: 'invalid', fields: { email: 'invalid_email' } }),
    }))
    await expect(post('/contact')).rejects.toMatchObject({ status: 422, error: 'invalid', fields: { email: 'invalid_email' } })
  })

  it('reports network failures and non-JSON errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    await expect(post('/contact')).rejects.toMatchObject({ status: 0, error: 'network' })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 502, json: async () => { throw new Error() } }))
    await expect(post('/contact')).rejects.toMatchObject({ status: 502, error: 'server_error' })
  })

  it('maps errors to messages', () => {
    expect(errorMessage(new ApiError(429, 'rate_limited'), FE)).toBe('R')
    expect(errorMessage(new ApiError(422, 'invalid'), FE)).toBe('I')
    expect(errorMessage(new ApiError(0, 'network'), FE)).toBe('N')
    expect(errorMessage(new ApiError(500, 'server_error'), FE)).toBe('N')
  })
})
