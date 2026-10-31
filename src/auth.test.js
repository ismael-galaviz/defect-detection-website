import { beforeEach, describe, expect, it } from 'vitest'
import { isValidEmail, isValidUsername, login, registerUser, verifyEmailToken } from './auth.js'

// Minimal in-memory localStorage: the auth simulation only needs get/set/remove.
beforeEach(() => {
  const store = new Map()
  globalThis.localStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  }
})

const user = { firstName: 'Ana', lastName: 'Ruiz', email: 'ana@example.com', username: 'ana.ruiz', password: 'a-long-password-1' }

describe('auth validators', () => {
  it('validates emails and usernames', () => {
    expect(isValidEmail(' ana@example.com ')).toBe(true)
    expect(isValidEmail('ana@example')).toBe(false)
    expect(isValidUsername('ana.ruiz')).toBe(true)
    expect(isValidUsername('ab')).toBe(false)
  })
})

describe('register → verify → login', () => {
  it('blocks login until the email is verified', async () => {
    const { token } = await registerUser(user)
    expect(await login(user.username, user.password)).toEqual({ ok: false, error: 'unverified' })
    expect(verifyEmailToken(token)).toEqual({ ok: true })
    expect(await login(user.email, user.password)).toEqual({ ok: true })
  })

  it('does not reveal an already-registered email', async () => {
    await registerUser(user)
    expect(await registerUser({ ...user, username: 'other.user' })).toEqual({ ok: true })
  })

  it('locks the account after 5 failed attempts', async () => {
    const { token } = await registerUser(user)
    verifyEmailToken(token)
    for (let i = 0; i < 4; i++) await login(user.username, 'wrong')
    expect((await login(user.username, 'wrong')).error).toBe('locked')
    expect((await login(user.username, user.password)).error).toBe('locked')
  })
})
