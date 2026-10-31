import { useEffect, useState } from 'react'
import { useLanguage, localeFor } from './i18n.jsx'
import { Icon } from './icons.jsx'
import { useAuthSession } from './auth.js'

function formatDate(iso, lang) {
  return new Intl.DateTimeFormat(localeFor(lang), {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date(`${iso}T12:00:00`))
}

function formatCurrency(amount, currency, lang) {
  return new Intl.NumberFormat(localeFor(lang), { style: 'currency', currency }).format(Number(amount))
}

function SupportTicketForm({ s }) {
  const [subject, setSubject] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState('normal')
  const [sent, setSent] = useState(false)

  function handleSubmit(e) {
    e.preventDefault()
    setSent(true)
  }

  if (sent) {
    return <div className="form-success"><p>{s.sentMessage}</p></div>
  }

  return (
    <form className="ticket-form" onSubmit={handleSubmit}>
      <div className="form-row">
        <label htmlFor="ticketSubject">{s.ticketSubject}</label>
        <input
          id="ticketSubject"
          type="text"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder={s.ticketSubjectPlaceholder}
          required
        />
      </div>
      <div className="form-row">
        <label htmlFor="ticketDescription">{s.ticketDescription}</label>
        <textarea
          id="ticketDescription"
          rows="3"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder={s.ticketDescriptionPlaceholder}
          required
        />
      </div>
      <div className="form-row">
        <label htmlFor="ticketPriority">{s.ticketPriority}</label>
        <select id="ticketPriority" value={priority} onChange={(e) => setPriority(e.target.value)}>
          <option value="low">{s.priorityOptions.low}</option>
          <option value="normal">{s.priorityOptions.normal}</option>
          <option value="high">{s.priorityOptions.high}</option>
        </select>
      </div>
      <button type="submit" className="btn btn-dark">{s.ticketSubmit}</button>
    </form>
  )
}

export default function VisionHomePage() {
  const { t, lang } = useLanguage()
  const v = t.auth.visionHome
  const { status, me } = useAuthSession()
  const [showAllPayments, setShowAllPayments] = useState(false)
  const [supportOpen, setSupportOpen] = useState(false)

  useEffect(() => {
    if (status === 'out') window.location.hash = '#/login'
  }, [status])

  if (status !== 'in') {
    return (
      <main>
        <section className="demo-section">
          <div className="container">
            {status === 'error'
              ? <div className="field-error-panel" role="alert"><p>{v.loadError}</p></div>
              : <p role="status">{v.loading}</p>}
          </div>
        </section>
      </main>
    )
  }

  const { user, subscriptions, payments } = me
  const activeCount = subscriptions.filter((s) => s.status === 'active').length
  const lastPayment = payments[0] // newest first, from the API

  return (
    <main>
      <section className="demo-hero">
        <div className="container">
          <span className="eyebrow">{me.company.name}</span>
          <h1>{v.greeting.replace('{name}', user.name.split(' ')[0])}</h1>
        </div>
      </section>

      <section className="demo-section">
        <div className="container">
          <nav className="breadcrumb" aria-label="Breadcrumb">
            <a href="#">{t.nav.home}</a>
            <span className="breadcrumb-sep" aria-hidden="true">/</span>
            <span aria-current="page">{v.eyebrow}</span>
          </nav>

          {subscriptions.length === 0 ? (
            <div className="vh-empty-state">
              <h2>{v.noAccount.title}</h2>
              <p>{v.noAccount.body}</p>
              <div className="vh-empty-actions">
                <a className="btn btn-dark" href="#contact">{v.noAccount.contactAgent}</a>
              </div>
            </div>
          ) : (
            <div className="vh-grid">
              <div className="vh-card">
                <div className="vh-card-icon"><Icon name="clipboard" /></div>
                <div className="vh-card-label">{v.subscriptions.title}</div>
                <div className="vh-card-value">{v.subscriptions.count.replace('{count}', activeCount)}</div>
                <ul className="vh-sub-list">
                  {subscriptions.map((sub, i) => (
                    <li key={i}>
                      <span>{sub.name}</span>
                      <span className="vh-pill">{v.status[sub.status]}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="vh-card">
                <div className="vh-card-icon"><Icon name="clock" /></div>
                <div className="vh-card-label">{v.payments.title}</div>
                {lastPayment ? (
                  <>
                    <div className="vh-card-value">
                      {v.payments.last}: {formatDate(lastPayment.paid_on, lang)} — {formatCurrency(lastPayment.amount, lastPayment.currency, lang)}
                    </div>
                    {payments.length > 1 && (
                      <button type="button" className="vh-link-btn" onClick={() => setShowAllPayments((s) => !s)}>
                        {v.payments.viewAll}
                      </button>
                    )}
                    {showAllPayments && (
                      <ul className="vh-detail-list">
                        {payments.map((p, i) => (
                          <li key={i}>{formatDate(p.paid_on, lang)} — {formatCurrency(p.amount, p.currency, lang)}</li>
                        ))}
                      </ul>
                    )}
                  </>
                ) : (
                  <p>{v.payments.empty}</p>
                )}
              </div>
            </div>
          )}

          <div className="vh-grid vh-grid-actions">
            <div className="vh-card">
              <div className="vh-card-icon"><Icon name="gear" /></div>
              <h3>{v.support.title}</h3>
              <p>{v.support.body}</p>
              {!supportOpen ? (
                <button type="button" className="btn btn-outline" onClick={() => setSupportOpen(true)}>
                  {v.support.cta}
                </button>
              ) : (
                <SupportTicketForm s={v.support} />
              )}
              <p className="field-hint">{v.support.responseTime}</p>
            </div>

            <div className="vh-card">
              <div className="vh-card-icon"><Icon name="clock" /></div>
              <h3>{v.appointment.title}</h3>
              <p>{v.appointment.body}</p>
              <a className="btn btn-outline" href="#contact">{v.appointment.cta}</a>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}
