import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import * as auth from './auth.js'

function respond(status, body = {}) {
  return { ok: status < 400, status, json: async () => body }
}

beforeEach(() => auth._resetForTests())
afterEach(() => vi.unstubAllGlobals())

describe('passwordProblem', () => {
  it('mirrors the server policy for instant feedback', () => {
    expect(auth.passwordProblem('short', 'short')).toBe('passwordShort')
    expect(auth.passwordProblem('password123456', 'password123456')).toBe('passwordCommon')
    expect(auth.passwordProblem('correct horse battery', 'correct horse batterx')).toBe('passwordMismatch')
    expect(auth.passwordProblem('correct horse battery', 'correct horse battery')).toBe(null)
  })
})

describe('session state', () => {
  it('signs in, loads /me, and signs out', async () => {
    const me = { user: { name: 'Ana' }, company: { name: 'X' }, subscriptions: [], payments: [], tickets: [] }
    const fetch = vi.fn()
      .mockResolvedValueOnce(respond(204))
      .mockResolvedValueOnce(respond(200, me))
      .mockResolvedValueOnce(respond(204))
    vi.stubGlobal('fetch', fetch)

    expect(await auth.login(' Ana@Example.com ', 'pw')).toEqual({ ok: true })
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({ email: 'ana@example.com', password: 'pw' })
    expect(auth.getAuthState()).toEqual({ status: 'in', me })

    await auth.logout()
    expect(auth.getAuthState()).toEqual({ status: 'out', me: null })
  })

  it('reports lockout with minutes to wait', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(respond(429, { error: 'locked', retry_after: 61 })))
    expect(await auth.login('a@b.co', 'pw')).toEqual({ ok: false, error: 'locked', minutes: 2 })
  })

  it('treats 401 from /me as signed out and other failures as an error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(respond(401, { error: 'unauthenticated' })))
    await auth.refreshSession()
    expect(auth.getAuthState().status).toBe('out')
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    await auth.refreshSession()
    expect(auth.getAuthState().status).toBe('error')
  })
})
