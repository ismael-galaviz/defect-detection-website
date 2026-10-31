import { useEffect, useState } from 'react'
import { useLanguage, localeFor } from './i18n.jsx'
import { Icon } from './icons.jsx'
import { refreshSession, useAuthSession } from './auth.js'
import { ApiError, errorMessage, post, upload } from './api.js'
import { ACCEPT, fileProblem } from './tickets.js'

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

function SupportTicketForm({ s, formErrors }) {
  const [subject, setSubject] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState('medium')
  const [files, setFiles] = useState([])
  const [error, setError] = useState(null)
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)

  function fileMessage(problem) {
    return s[problem.key].replace('{file}', problem.file || '')
  }

  function handleFiles(e) {
    const chosen = Array.from(e.target.files)
    const problem = fileProblem(chosen)
    setError(problem ? fileMessage(problem) : null)
    setFiles(problem ? [] : chosen)
    if (problem) e.target.value = ''
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSending(true)
    try {
      const ids = []
      for (const file of files) {
        try {
          ids.push((await upload('/attachments', file)).id)
        } catch (err) {
          if (err.error === 'too_large') throw new Error(fileMessage({ key: 'tooLarge', file: file.name }))
          if (err.error === 'unsupported_type') throw new Error(fileMessage({ key: 'unsupportedType', file: file.name }))
          throw err
        }
      }
      await post('/tickets', { subject, description, priority, attachment_ids: ids })
      setSent(true)
      refreshSession() // reload Vision Home so the new ticket appears in the list
    } catch (err) {
      setError(err instanceof ApiError ? errorMessage(err, formErrors) : err.message)
    } finally {
      setSending(false)
    }
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
          maxLength={200}
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
          maxLength={5000}
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
          <option value="medium">{s.priorityOptions.medium}</option>
          <option value="high">{s.priorityOptions.high}</option>
        </select>
      </div>
      <div className="form-row">
        <label htmlFor="ticketFiles">{s.attachLabel}</label>
        <input id="ticketFiles" type="file" multiple accept={ACCEPT.join(',')} onChange={handleFiles} />
        <p className="field-hint">{s.attachHint}</p>
      </div>
      {error && <p className="field-error" role="alert">{error}</p>}
      <button type="submit" className="btn btn-dark" disabled={sending}>
        {sending ? s.ticketSubmitting : s.ticketSubmit}
      </button>
    </form>
  )
}

function TicketList({ tickets, s, lang }) {
  if (tickets.length === 0) return <p>{s.noTickets}</p>
  return (
    <ul className="vh-detail-list vh-ticket-list">
      {tickets.map((tk) => (
        <li key={tk.id}>
          <div>
            <strong>#{tk.id} · {tk.subject}</strong>{' '}
            <span className="vh-pill">{s.ticketStatus[tk.status]}</span>
          </div>
          <div className="field-hint">
            {formatDate(tk.created_at.slice(0, 10), lang)} · {s.ticketPriority}: {s.priorityOptions[tk.priority]}
          </div>
          {tk.attachments.map((f) => (
            <div key={f.id}><a href={`/api/attachments/${f.id}`} download={f.filename}>{f.filename}</a></div>
          ))}
        </li>
      ))}
    </ul>
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
                <SupportTicketForm s={v.support} formErrors={t.formErrors} />
              )}
              <p className="field-hint">{v.support.responseTime}</p>
              <h4>{v.support.ticketsTitle}</h4>
              <TicketList tickets={me.tickets} s={v.support} lang={lang} />
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
