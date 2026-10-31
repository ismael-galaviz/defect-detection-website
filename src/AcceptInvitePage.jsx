import { useEffect, useState } from 'react'
import { useLanguage } from './i18n.jsx'
import { Icon } from './icons.jsx'
import { acceptInvite, getInvite, passwordProblem } from './auth.js'
import { errorMessage } from './api.js'

function getTokenFromHash() {
  return new URLSearchParams(window.location.hash.split('?')[1] || '').get('token') || ''
}

// #/accept-invite?token=… — the link staff send with `python -m app.cli invite`.
export default function AcceptInvitePage() {
  const { t } = useLanguage()
  const a = t.auth.acceptInvite
  const r = t.auth.resetPassword
  const [token] = useState(getTokenFromHash)
  const [invite, setInvite] = useState(undefined) // undefined = loading, null = invalid
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    getInvite(token).then((res) => setInvite(res.ok ? res.invite : null))
  }, [token])

  async function handleSubmit(e) {
    e.preventDefault()
    const problem = passwordProblem(password, confirmPassword)
    if (problem) return setError(r.errors[problem])
    setError(null)
    setSubmitting(true)
    const res = await acceptInvite(token, password)
    setSubmitting(false)
    if (res.ok) {
      window.location.hash = '#/vision-home'
    } else if (res.error === 'link_expired') {
      setInvite(null)
    } else if (res.fields?.password) {
      setError(r.errors.passwordCommon)
    } else {
      setError(errorMessage(res, t.formErrors))
    }
  }

  const hero = (title) => (
    <section className="demo-hero">
      <div className="container">
        <span className="eyebrow">{a.eyebrow}</span>
        <h1>{title}</h1>
      </div>
    </section>
  )

  if (invite === undefined) {
    return <main>{hero(a.title)}<section className="demo-section"><div className="container auth-shell"><p role="status">{a.loading}</p></div></section></main>
  }

  if (invite === null) {
    return (
      <main>
        {hero(a.invalidTitle)}
        <section className="demo-section">
          <div className="container auth-shell">
            <div className="field-error-panel"><p>{a.invalidBody}</p></div>
            <p className="auth-switch"><a href="#contact">{t.auth.visionHome.noAccount.contactAgent}</a></p>
          </div>
        </section>
      </main>
    )
  }

  return (
    <main>
      {hero(a.title)}
      <section className="demo-section">
        <div className="container auth-shell">
          <form className="lead-form auth-card" onSubmit={handleSubmit}>
            <p>{a.intro.replace('{company}', invite.company).replace('{email}', invite.email)}</p>
            <input type="email" value={invite.email} autoComplete="username" readOnly hidden />
            <div className="form-row">
              <label htmlFor="newPassword">{r.newPassword}</label>
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
              <label htmlFor="confirmPassword">{r.confirmPassword}</label>
              <input
                id="confirmPassword"
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
            {error && <p className="field-error" role="alert">{error}</p>}
            <button type="submit" className="btn btn-dark" style={{ width: '100%' }} disabled={submitting}>
              {submitting ? a.submitting : a.submit}
            </button>
          </form>
        </div>
      </section>
    </main>
  )
}
