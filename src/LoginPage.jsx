import { useState } from 'react'
import { useLanguage } from './i18n.jsx'
import { Icon } from './icons.jsx'
import { login } from './auth.js'
import { errorMessage } from './api.js'

export default function LoginPage() {
  const { t } = useLanguage()
  const a = t.auth
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    const result = await login(email, password)
    setSubmitting(false)
    if (result.ok) {
      window.location.hash = '#/vision-home'
      return
    }
    if (result.error === 'locked') setError(a.login.errors.locked.replace('{minutes}', result.minutes))
    else if (result.error === 'invalid_credentials' || result.error === 'invalid') setError(a.login.errors.invalid_credentials)
    else setError(errorMessage(result, t.formErrors))
  }

  return (
    <main>
      <section className="demo-hero">
        <div className="container">
          <span className="eyebrow">{a.login.eyebrow}</span>
          <h1>{a.login.title}</h1>
        </div>
      </section>

      <section className="demo-section">
        <div className="container auth-shell">
          <form className="lead-form auth-card" onSubmit={handleSubmit}>
            <div className="form-row">
              <label htmlFor="email">{a.login.identifier}</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={a.login.identifierPlaceholder}
                autoComplete="username"
                required
              />
            </div>
            <div className="form-row">
              <label htmlFor="password">{a.login.password}</label>
              <div className="password-field">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={a.login.passwordPlaceholder}
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? a.login.hidePassword : a.login.showPassword}
                >
                  <Icon name={showPassword ? 'eyeOff' : 'eye'} size={18} />
                </button>
              </div>
            </div>

            {error && <p className="field-error" role="alert">{error}</p>}

            <button type="submit" className="btn btn-dark" style={{ width: '100%' }} disabled={submitting}>
              {submitting ? a.login.submitting : a.login.submit}
            </button>

            <div className="auth-links">
              <a href="#/forgot-password">{a.login.forgotPassword}</a>
            </div>
            <p className="auth-switch">{a.login.inviteOnly}</p>
          </form>
        </div>
      </section>
    </main>
  )
}
