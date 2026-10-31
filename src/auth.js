// Client-only, localStorage-backed auth simulation. There is no backend in this repo (see docs/architecture/SDD.md
// §11/§14) — this exists so the Login/Register/Recovery/Vision Home screens are fully clickable in the
// demo, not to provide real security. Passwords never leave the browser, but SHA-256 in JS is not a
// substitute for server-side bcrypt/Argon2, and nothing here is rate-limited or audited server-side.

import { useEffect, useState } from 'react'

const listeners = new Set()
function notifyAuthChange() {
  listeners.forEach((fn) => fn())
}

export function useAuthSession() {
  const [session, setSession] = useState(() => getSession())
  useEffect(() => {
    const onChange = () => setSession(getSession())
    listeners.add(onChange)
    window.addEventListener('storage', onChange)
    return () => {
      listeners.delete(onChange)
      window.removeEventListener('storage', onChange)
    }
  }, [])
  return session
}

const USERS_KEY = 'veritx-auth-users'
const SESSION_KEY = 'veritx-auth-session'
const VERIFY_TOKENS_KEY = 'veritx-auth-verify-tokens'
const RESET_TOKENS_KEY = 'veritx-auth-reset-tokens'
const ATTEMPTS_KEY = 'veritx-auth-attempts'

const DUMMY_USERNAME = 'test'
const DUMMY_PASSWORD = 'vision'

const MAX_ATTEMPTS = 5
const LOCKOUT_MS = 60 * 1000
const VERIFY_TOKEN_TTL_MS = 24 * 60 * 60 * 1000
const RESET_TOKEN_TTL_MS = 30 * 60 * 1000

const COMMON_PASSWORDS = [
  'password123456', '123456789012', 'qwertyuiop123', 'letmein123456',
  'admin12345678', 'welcome123456', 'iloveyou123456',
]

// Vite replaces import.meta.env.DEV with `false` in production builds, so this branch (and every UI
// path that checks it) is dead code — and therefore unreachable — once built for production.
export const IS_DUMMY_LOGIN_ENABLED = import.meta.env.DEV

export const DEMO_ACCOUNT = {
  status: 'active',
  subscriptions: [
    { name: 'Vision A — Final Inspection Line', status: 'active' },
    { name: 'Vision A — Finishing Line', status: 'active' },
  ],
  payments: [
    { date: '2026-09-05', amount: 8500, currency: 'MXN' },
    { date: '2026-10-05', amount: 8500, currency: 'MXN' },
  ],
}

function readJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function writeJSON(key, value) {
  localStorage.setItem(key, JSON.stringify(value))
}

async function sha256(text) {
  const data = new TextEncoder().encode(text)
  const digest = await crypto.subtle.digest('SHA-256', data)
  return Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, '0')).join('')
}

function randomToken() {
  const bytes = crypto.getRandomValues(new Uint8Array(24))
  return Array.from(bytes).map((b) => b.toString(16).padStart(2, '0')).join('')
}

function getUsers() {
  return readJSON(USERS_KEY, [])
}

function saveUsers(users) {
  writeJSON(USERS_KEY, users)
}

function findUserByEmail(email) {
  const e = email.trim().toLowerCase()
  return getUsers().find((u) => u.email.toLowerCase() === e)
}

function findUserByUsername(username) {
  const u = username.trim().toLowerCase()
  return getUsers().find((x) => x.username.toLowerCase() === u)
}

function findUserByIdentifier(identifier) {
  return findUserByEmail(identifier) || findUserByUsername(identifier)
}

export function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())
}

export function isValidUsername(username) {
  return /^[a-zA-Z0-9_.-]{4,30}$/.test(username.trim())
}

export function isPasswordCommon(password) {
  return COMMON_PASSWORDS.includes(password.toLowerCase())
}

function getAttempts(id) {
  const map = readJSON(ATTEMPTS_KEY, {})
  return map[id] || { count: 0, lockedUntil: 0 }
}

function setAttempts(id, entry) {
  const map = readJSON(ATTEMPTS_KEY, {})
  map[id] = entry
  writeJSON(ATTEMPTS_KEY, map)
}

function clearAttempts(id) {
  const map = readJSON(ATTEMPTS_KEY, {})
  delete map[id]
  writeJSON(ATTEMPTS_KEY, map)
}

function createVerifyToken(username) {
  const tokens = readJSON(VERIFY_TOKENS_KEY, [])
  const token = randomToken()
  tokens.push({ token, username, expiresAt: Date.now() + VERIFY_TOKEN_TTL_MS })
  writeJSON(VERIFY_TOKENS_KEY, tokens)
  return token
}

export async function registerUser({ firstName, lastName, email, username, password }) {
  if (findUserByEmail(email)) {
    // Email already registered — return success anyway so the response doesn't reveal that.
    return { ok: true }
  }
  if (findUserByUsername(username)) {
    return { ok: false, error: 'username_taken' }
  }
  const users = getUsers()
  users.push({
    firstName,
    lastName,
    email,
    username,
    passwordHash: await sha256(password),
    verified: false,
    createdAt: new Date().toISOString(),
    account: null,
  })
  saveUsers(users)
  return { ok: true, token: createVerifyToken(username) }
}

export function verifyEmailToken(token) {
  const tokens = readJSON(VERIFY_TOKENS_KEY, [])
  const entry = tokens.find((t) => t.token === token)
  if (!entry) return { ok: false, error: 'invalid' }
  if (entry.expiresAt < Date.now()) return { ok: false, error: 'expired' }
  const users = getUsers()
  const user = users.find((u) => u.username === entry.username)
  if (!user) return { ok: false, error: 'invalid' }
  // Deliberately idempotent (token is kept, not deleted, until it expires): React StrictMode
  // double-invokes effects in dev, and a real inbox click + a stale/reloaded tab can both replay
  // the same link. Re-verifying an already-verified user must succeed, not report "invalid".
  if (!user.verified) {
    user.verified = true
    saveUsers(users)
  }
  return { ok: true }
}

export async function login(identifier, password) {
  const id = identifier.trim().toLowerCase()

  if (IS_DUMMY_LOGIN_ENABLED && id === DUMMY_USERNAME && password === DUMMY_PASSWORD) {
    writeJSON(SESSION_KEY, { username: DUMMY_USERNAME, isDummy: true, loginAt: Date.now() })
    notifyAuthChange()
    return { ok: true }
  }

  const attempt = getAttempts(id)
  if (attempt.lockedUntil > Date.now()) {
    return { ok: false, error: 'locked', retryAt: attempt.lockedUntil }
  }

  const user = findUserByIdentifier(identifier)
  const passwordHash = user ? await sha256(password) : null
  const valid = !!user && user.verified && passwordHash === user.passwordHash

  if (!valid) {
    const count = attempt.count + 1
    const locked = count >= MAX_ATTEMPTS
    setAttempts(id, { count, lockedUntil: locked ? Date.now() + LOCKOUT_MS : 0 })
    if (locked) return { ok: false, error: 'locked', retryAt: Date.now() + LOCKOUT_MS }
    if (user && !user.verified) return { ok: false, error: 'unverified' }
    return { ok: false, error: 'invalid_credentials' }
  }

  clearAttempts(id)
  writeJSON(SESSION_KEY, { username: user.username, isDummy: false, loginAt: Date.now() })
  notifyAuthChange()
  return { ok: true }
}

export function getSession() {
  return readJSON(SESSION_KEY, null)
}

export function logout() {
  localStorage.removeItem(SESSION_KEY)
  notifyAuthChange()
}

export function getCurrentUser() {
  const session = getSession()
  if (!session) return null
  if (session.isDummy) {
    return {
      username: DUMMY_USERNAME,
      firstName: 'Modo',
      lastName: 'Prueba',
      email: 'demo@veritxvision.com',
      verified: true,
      account: DEMO_ACCOUNT,
      isDummy: true,
    }
  }
  const user = findUserByUsername(session.username)
  return user ? { ...user, isDummy: false } : null
}

export function requestPasswordReset(identifier) {
  const user = findUserByIdentifier(identifier)
  if (!user) return { ok: true }
  const tokens = readJSON(RESET_TOKENS_KEY, [])
  const token = randomToken()
  tokens.push({ token, username: user.username, expiresAt: Date.now() + RESET_TOKEN_TTL_MS })
  writeJSON(RESET_TOKENS_KEY, tokens)
  return { ok: true, token }
}

export function validateResetToken(token) {
  const tokens = readJSON(RESET_TOKENS_KEY, [])
  const entry = tokens.find((t) => t.token === token)
  if (!entry) return { ok: false, error: 'invalid' }
  if (entry.expiresAt < Date.now()) return { ok: false, error: 'expired' }
  return { ok: true, username: entry.username }
}

export async function resetPassword(token, newPassword) {
  const check = validateResetToken(token)
  if (!check.ok) return check
  const users = getUsers()
  const user = users.find((u) => u.username === check.username)
  if (!user) return { ok: false, error: 'invalid' }
  user.passwordHash = await sha256(newPassword)
  saveUsers(users)
  writeJSON(RESET_TOKENS_KEY, readJSON(RESET_TOKENS_KEY, []).filter((t) => t.token !== token))
  clearAttempts(user.username)
  logout()
  return { ok: true }
}

export function recoverUsername(email) {
  const user = findUserByEmail(email)
  if (!user) return { ok: true }
  return { ok: true, username: user.username }
}
