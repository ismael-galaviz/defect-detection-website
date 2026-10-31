// Customer-portal session, backed by the real API (server/app/routes/auth.py). The session
// lives in an HttpOnly cookie the browser sends to /api automatically; this module only keeps
// the result of GET /api/me in memory so components can render it.

import { useEffect, useState } from 'react'
import { ApiError, get, post } from './api.js'

// Same rules as the server (server/app/security.py), for instant feedback only.
const COMMON_PASSWORDS = new Set([
  'password123456', '123456789012', 'qwertyuiop123', 'letmein123456', 'admin12345678',
  'welcome123456', 'iloveyou123456', 'contraseña123', 'contrasena123', '123456789abc',
  'passwordpassword', 'qwertyqwerty', 'abc123abc123', 'veritxvision1', 'veritxvision123',
])

export function passwordProblem(password, confirm) {
  if (password.length < 12) return 'passwordShort'
  if (COMMON_PASSWORDS.has(password.toLowerCase())) return 'passwordCommon'
  if (password !== confirm) return 'passwordMismatch'
  return null
}

// status: 'unknown' (not checked yet) | 'in' | 'out' | 'error' (couldn't reach the server)
let state = { status: 'unknown', me: null }
const listeners = new Set()

function setState(next) {
  state = next
  listeners.forEach((fn) => fn(state))
}

export function getAuthState() {
  return state
}

export function _resetForTests() {
  state = { status: 'unknown', me: null }
}

export async function refreshSession() {
  try {
    setState({ status: 'in', me: await get('/me') })
  } catch (err) {
    setState({ status: err.status === 401 ? 'out' : 'error', me: null })
  }
}

// Returns { status, me }; checks the session once on first use.
export function useAuthSession() {
  const [current, setCurrent] = useState(state)
  useEffect(() => {
    listeners.add(setCurrent)
    if (state.status === 'unknown') refreshSession()
    else setCurrent(state)
    return () => listeners.delete(setCurrent)
  }, [])
  return current
}

async function attempt(fn) {
  try {
    await fn()
    return { ok: true }
  } catch (err) {
    if (!(err instanceof ApiError)) throw err
    return { ok: false, error: err.error, fields: err.fields }
  }
}

export async function login(email, password) {
  try {
    await post('/auth/login', { email: email.trim().toLowerCase(), password })
  } catch (err) {
    if (err.error === 'locked') {
      return { ok: false, error: 'locked', minutes: Math.max(1, Math.ceil((err.retry_after || 60) / 60)) }
    }
    return { ok: false, error: err.error }
  }
  await refreshSession()
  return { ok: true }
}

export async function logout() {
  await post('/auth/logout').catch(() => {})
  setState({ status: 'out', me: null })
}

export async function getInvite(token) {
  try {
    return { ok: true, invite: await get(`/auth/invite/${encodeURIComponent(token)}`) }
  } catch (err) {
    return { ok: false, error: err.error }
  }
}

export async function acceptInvite(token, password) {
  const result = await attempt(() => post('/auth/accept-invite', { token, password }))
  if (result.ok) await refreshSession()
  return result
}

export const requestPasswordReset = (email, lang) =>
  attempt(() => post('/auth/forgot', { email: email.trim(), lang }))

export const resetPassword = (token, password) =>
  attempt(() => post('/auth/reset', { token, password }))
