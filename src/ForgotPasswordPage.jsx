import { useEffect, useRef, useState } from 'react'
import { useLanguage } from './i18n.jsx'
import { Icon } from './icons.jsx'
import { passwordProblem, requestPasswordReset, resetPassword } from './auth.js'
import { errorMessage } from './api.js'

function getTokenFromHash() {
  const query = window.location.hash.split('?')[1] || ''
  return new URLSearchParams(query).get('token') || ''
}

export default function ForgotPasswordPage() {
  const token = getTokenFromHash()
  return token ? <ResetPasswordView token={token} /> : <RequestView />
}

function RequestView() {
  const { t, lang } = useLanguage()
  const a = t.auth.forgotPassword
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const resultRef = useRef(null)

  useEffect(() => {
    if (result) resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [result])

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    const res = await requestPasswordReset(email, lang)
    setSubmitting(false)
    if (res.ok) setResult(res)
    else setError(errorMessage(res, t.formErrors))
  }

  return (
    <main>
      <section className="demo-hero">
        <div className="container">
          <span className="eyebrow">{a.eyebrow}</span>
          <h1>{a.title}</h1>
        </div>
      </section>
      <section className="demo-section">
        <div className="container auth-shell">
          {result ? (
            <div ref={resultRef}>
              <div className="form-success"><p>{a.genericMessage}</p></div>
              <p className="auth-switch"><a href="#/login">{a.backToLogin}</a></p>
            </div>
          ) : (
            <form className="lead-form auth-card" onSubmit={handleSubmit}>
              <div className="form-row">
                <label htmlFor="email">{a.identifier}</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={a.identifierPlaceholder}
                  autoComplete="email"
                  required
                />
              </div>
              {error && <p className="field-error" role="alert">{error}</p>}
              <button type="submit" className="btn btn-dark" style={{ width: '100%' }} disabled={submitting}>
                {submitting ? a.submitting : a.submit}
              </button>
              <p className="auth-switch"><a href="#/login">{a.backToLogin}</a></p>
            </form>
          )}
        </div>
      </section>
    </main>
  )
}

function ResetPasswordView({ token }) {
  const { t } = useLanguage()
  const a = t.auth.resetPassword
  // The server validates the link on submit (it can't be checked without using it up).
  const [invalid, setInvalid] = useState(false)
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)
  const doneRef = useRef(null)

  useEffect(() => {
    if (done) doneRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [done])

  async function handleSubmit(e) {
    e.preventDefault()
    const problem = passwordProblem(password, confirmPassword)
    if (problem) return setError(a.errors[problem])
    setError(null)
    setSubmitting(true)
    const res = await resetPassword(token, password)
    setSubmitting(false)
    if (res.ok) setDone(true)
    else if (res.error === 'link_expired') setInvalid(true)
    else if (res.fields?.password) setError(a.errors.passwordCommon)
    else setError(errorMessage(res, t.formErrors))
  }

  if (invalid) {
    return (
      <main>
        <section className="demo-hero">
          <div className="container">
            <span className="eyebrow">{t.auth.forgotPassword.eyebrow}</span>
            <h1>{a.invalidTitle}</h1>
          </div>
        </section>
        <section className="demo-section">
          <div className="container auth-shell">
            <div className="field-error-panel"><p>{a.invalidBody}</p></div>
            <p className="auth-switch"><a href="#/forgot-password">{a.requestNew}</a></p>
          </div>
        </section>
      </main>
    )
  }

  if (done) {
    return (
      <main>
        <section className="demo-hero">
          <div className="container">
            <span className="eyebrow">{t.auth.forgotPassword.eyebrow}</span>
            <h1>{a.successTitle}</h1>
          </div>
        </section>
        <section className="demo-section">
          <div className="container auth-shell" ref={doneRef}>
            <div className="form-success"><p>{a.successBody}</p></div>
            <p className="auth-switch"><a href="#/login">{a.goToLogin}</a></p>
          </div>
        </section>
      </main>
    )
  }

  return (
    <main>
      <section className="demo-hero">
        <div className="container">
          <span className="eyebrow">{t.auth.forgotPassword.eyebrow}</span>
          <h1>{a.title}</h1>
        </div>
      </section>
      <section className="demo-section">
        <div className="container auth-shell">
          <form className="lead-form auth-card" onSubmit={handleSubmit}>
            <div className="form-row">
              <label htmlFor="newPassword">{a.newPassword}</label>
              <div className="password-field">
                <input
                  id="newPassword"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? t.auth.login.hidePassword : t.auth.login.showPassword}
                >
                  <Icon name={showPassword ? 'eyeOff' : 'eye'} size={18} />
                </button>
              </div>
            </div>
            <div className="form-row">
              <label htmlFor="confirmPassword">{a.confirmPassword}</label>
              <input
                id="confirmPassword"
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
            {error && <p className="field-error">{error}</p>}
            <button type="submit" className="btn btn-dark" style={{ width: '100%' }} disabled={submitting}>
              {submitting ? a.submitting : a.submit}
            </button>
          </form>
        </div>
      </section>
    </main>
  )
}
