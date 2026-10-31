import { useEffect, useMemo, useRef, useState } from 'react'
import { LanguageProvider, useLanguage, localeFor } from './i18n.jsx'
import { Icon } from './icons.jsx'
import { errorMessage, post } from './api.js'
import { useAuthSession, logout } from './auth.js'
import DemoPage from './DemoPage.jsx'
import CalculatorPage from './CalculatorPage.jsx'
import AboutPage from './AboutPage.jsx'
import LoginPage from './LoginPage.jsx'
import RegisterPage from './RegisterPage.jsx'
import VerifyEmailPage from './VerifyEmailPage.jsx'
import ForgotPasswordPage from './ForgotPasswordPage.jsx'
import RecoverUsernamePage from './RecoverUsernamePage.jsx'
import VisionHomePage from './VisionHomePage.jsx'
import PrivacyPolicyPage from './PrivacyPolicyPage.jsx'

const SATELLITE_ROUTES = [
  'demo', 'calculator', 'about', 'privacy',
  'login', 'register', 'verify-email', 'forgot-password', 'recover-username', 'vision-home',
]

function useRoute() {
  const [hash, setHash] = useState(window.location.hash)
  useEffect(() => {
    const onHash = () => setHash(window.location.hash)
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])
  if (hash.startsWith('#/demo')) return 'demo'
  if (hash.startsWith('#/calculator')) return 'calculator'
  if (hash.startsWith('#/about')) return 'about'
  if (hash.startsWith('#/privacy')) return 'privacy'
  if (hash.startsWith('#/login')) return 'login'
  if (hash.startsWith('#/register')) return 'register'
  if (hash.startsWith('#/verify-email')) return 'verify-email'
  if (hash.startsWith('#/forgot-password')) return 'forgot-password'
  if (hash.startsWith('#/recover-username')) return 'recover-username'
  if (hash.startsWith('#/vision-home')) return 'vision-home'
  return 'home'
}

function LangSwitch() {
  const { lang, setLang } = useLanguage()
  return (
    <select
      className="lang-switch"
      value={lang}
      onChange={(e) => setLang(e.target.value)}
      aria-label="Language / Idioma"
    >
      <option value="es">🇲🇽 ES</option>
      <option value="en">🇺🇸 EN</option>
      <option value="fr">🇫🇷 FR</option>
    </select>
  )
}

function NavDropdown({ label, items, isOpen, onToggle, onNavigate }) {
  return (
    <div className="nav-dropdown">
      <button
        type="button"
        className="nav-dropdown-trigger"
        aria-haspopup="true"
        aria-expanded={isOpen}
        onClick={onToggle}
      >
        {label}
        <span className={`chev${isOpen ? ' open' : ''}`}><Icon name="chevronDown" size={14} /></span>
      </button>
      {isOpen && (
        <div className="nav-dropdown-panel">
          {items.map((i) => (
            <a key={i.href} href={i.href} onClick={onNavigate}>{i.label}</a>
          ))}
        </div>
      )}
    </div>
  )
}

function MobileAccordion({ label, items, onNavigate }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mobile-accordion">
      <button
        type="button"
        className="mobile-accordion-trigger"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        {label}
        <span className={`chev${open ? ' open' : ''}`}><Icon name="chevronDown" size={16} /></span>
      </button>
      {open && (
        <div className="mobile-accordion-panel">
          {items.map((i) => (
            <a key={i.href} href={i.href} onClick={onNavigate}>{i.label}</a>
          ))}
        </div>
      )}
    </div>
  )
}

function Header() {
  const { t } = useLanguage()
  const session = useAuthSession()
  const [menuOpen, setMenuOpen] = useState(false)
  const [openDropdown, setOpenDropdown] = useState(null)
  const navRef = useRef(null)
  const accountRef = useRef(null)
  const accountHref = session ? '#/vision-home' : '#/login'
  const accountLabel = session ? t.auth.navAccount : t.auth.navLogin

  useEffect(() => {
    if (!openDropdown) return
    function onDocClick(e) {
      const activeRef = openDropdown === 'account' ? accountRef : navRef
      if (activeRef.current && !activeRef.current.contains(e.target)) setOpenDropdown(null)
    }
    function onKey(e) {
      if (e.key === 'Escape') setOpenDropdown(null)
    }
    document.addEventListener('mousedown', onDocClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDocClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [openDropdown])

  function toggleDropdown(name) {
    setOpenDropdown((cur) => (cur === name ? null : name))
  }

  function handleLogout() {
    logout()
    setOpenDropdown(null)
    window.location.hash = '#/login'
  }

  return (
    <header className="site-header">
      <div className="container nav-wrap">
        <a href="#" className="logo">
          <span className="logo-mark" aria-hidden="true" />
          VeritX Vision
        </a>
        <nav className="nav-links" ref={navRef}>
          <a href="#">{t.nav.home}</a>
          <NavDropdown
            label={t.nav.product}
            items={t.nav.productItems}
            isOpen={openDropdown === 'product'}
            onToggle={() => toggleDropdown('product')}
            onNavigate={() => setOpenDropdown(null)}
          />
          <a href="#/calculator">{t.nav.calculator}</a>
          <NavDropdown
            label={t.nav.aboutLabel}
            items={t.nav.aboutItems}
            isOpen={openDropdown === 'about'}
            onToggle={() => toggleDropdown('about')}
            onNavigate={() => setOpenDropdown(null)}
          />
        </nav>
        <div className="nav-cta">
          <LangSwitch />
          {session ? (
            <div className="account-menu" ref={accountRef}>
              <button
                type="button"
                className="nav-account-link"
                aria-haspopup="true"
                aria-expanded={openDropdown === 'account'}
                aria-label={accountLabel}
                title={accountLabel}
                onClick={() => toggleDropdown('account')}
              >
                <Icon name="user" size={18} />
              </button>
              {openDropdown === 'account' && (
                <div className="nav-dropdown-panel account-menu-panel">
                  <a href="#/vision-home" onClick={() => setOpenDropdown(null)}>{t.auth.navAccount}</a>
                  <button type="button" onClick={handleLogout}>{t.auth.visionHome.logout}</button>
                </div>
              )}
            </div>
          ) : (
            <a href={accountHref} className="nav-account-link" aria-label={accountLabel} title={accountLabel}>
              <Icon name="user" size={18} />
            </a>
          )}
          <button
            type="button"
            className="mobile-toggle"
            aria-label="Menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((o) => !o)}
          >
            {menuOpen ? '✕' : '☰'}
          </button>
        </div>
      </div>
      {menuOpen && (
        <nav className="mobile-menu">
          <a href="#" onClick={() => setMenuOpen(false)}>{t.nav.home}</a>
          <MobileAccordion label={t.nav.product} items={t.nav.productItems} onNavigate={() => setMenuOpen(false)} />
          <a href="#/calculator" onClick={() => setMenuOpen(false)}>{t.nav.calculator}</a>
          <MobileAccordion label={t.nav.aboutLabel} items={t.nav.aboutItems} onNavigate={() => setMenuOpen(false)} />
          <a href={accountHref} onClick={() => setMenuOpen(false)}>{accountLabel}</a>
          {session && (
            <a
              href="#/login"
              onClick={(e) => {
                e.preventDefault()
                setMenuOpen(false)
                handleLogout()
              }}
            >
              {t.auth.visionHome.logout}
            </a>
          )}
        </nav>
      )}
    </header>
  )
}

function Hero() {
  const { t } = useLanguage()
  return (
    <section className="hero">
      <div className="container hero-grid">
        <div>
          <span className="eyebrow">{t.hero.eyebrow}</span>
          <h1>
            {t.hero.titleStart}<span className="accent">{t.hero.titleAccent}</span>
          </h1>
          <p className="lead">{t.hero.lead}</p>
          <div className="hero-actions">
            <a href="#contact" className="btn btn-primary">{t.hero.ctaPrimary}</a>
            <a href="#how-it-works" className="btn btn-ghost">{t.hero.ctaSecondary}</a>
          </div>
          <div className="hero-stats">
            {t.hero.stats.map((s) => (
              <div className="hero-stat" key={s.label}>
                <div className="num">{s.num}</div>
                <div className="label">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="hero-visual">
          <div className="scan-frame">
            <div className="scan-line" />
            {t.hero.defectTags.map((d) => (
              <div className="defect-tag" key={d.label} data-label={d.label} style={d.style} />
            ))}
          </div>
          <div className="hero-visual-caption">
            <span><span className="dot-live" />{t.hero.liveFeed}</span>
            <span>{t.hero.feedDetail}</span>
          </div>
        </div>
      </div>
    </section>
  )
}

function VisionA() {
  const { t } = useLanguage()
  return (
    <section id="vision-a" className="visiona-section">
      <div className="container visiona-grid">
        <div>
          <span className="eyebrow">{t.visionA.eyebrow}</span>
          <h2 className="section-title">{t.visionA.title}</h2>
          <p className="section-sub">{t.visionA.sub}</p>
          <div className="visiona-features">
            {t.visionA.features.map((f) => (
              <div className="visiona-feature" key={f.icon}>
                <div className="vf-icon"><Icon name={f.icon} /></div>
                <div>
                  <h4>{f.title}</h4>
                  <p>{f.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="visiona-visual">
          <div className="video-embed">
            <iframe
              src="https://www.youtube-nocookie.com/embed/djK5l04jRoM"
              title={t.visionA.videoTitle}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              allowFullScreen
            />
          </div>
        </div>
      </div>
    </section>
  )
}

function HowItWorks() {
  const { t } = useLanguage()
  return (
    <section id="how-it-works">
      <div className="container">
        <span className="eyebrow">{t.howItWorks.eyebrow}</span>
        <h2 className="section-title">{t.howItWorks.title}</h2>
        <p className="section-sub">{t.howItWorks.sub}</p>
        <div className="steps-grid">
          {t.howItWorks.steps.map((s) => (
            <div className="step-card" key={s.n}>
              <div className="step-num">{s.n}</div>
              <h4>{s.title}</h4>
              <p>{s.body}</p>
            </div>
          ))}
        </div>

        <div className="integration-card">
          <div className="integration-icon"><Icon name="gear" size={26} /></div>
          <div className="integration-body">
            <h4>{t.howItWorks.integration.title}</h4>
            <p>{t.howItWorks.integration.body}</p>
            <div className="integration-examples">
              {t.howItWorks.integration.examples.map((ex) => (
                <div className="integration-example" key={ex.action}>
                  <span className="ex-icon"><Icon name={ex.icon} size={18} /></span>
                  <p className="ex-text">
                    <strong>{ex.rule}</strong>
                    <span className="ex-arrow">→</span>
                    {ex.action}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function UseCases() {
  const { t } = useLanguage()
  return (
    <section id="use-cases" className="usecases-section">
      <div className="container">
        <span className="eyebrow">{t.useCases.eyebrow}</span>
        <h2 className="section-title">{t.useCases.title}</h2>
        <p className="section-sub">{t.useCases.sub}</p>
        <div className="usecases-grid">
          {t.useCases.cards.map((u) => (
            <div className="usecase-card" key={u.icon}>
              <div className="usecase-icon"><Icon name={u.icon} /></div>
              <h4>{u.title}</h4>
              <p>{u.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Comparison() {
  const { t } = useLanguage()
  return (
    <section id="comparison">
      <div className="container">
        <span className="eyebrow">{t.comparison.eyebrow}</span>
        <h2 className="section-title">{t.comparison.title}</h2>
        <p className="section-sub">{t.comparison.sub}</p>
        <div className="usecases-grid why-grid">
          {t.comparison.cards.map((c) => (
            <div className="usecase-card" key={c.title}>
              <div className="usecase-icon"><Icon name={c.icon} /></div>
              <h4>{c.title}</h4>
              <p>{c.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Specs() {
  const { t } = useLanguage()
  return (
    <section id="specs" className="specs-section">
      <div className="container">
        <span className="eyebrow" style={{ background: 'rgba(0,212,255,0.15)' }}>{t.specs.eyebrow}</span>
        <h2 className="section-title">{t.specs.title}</h2>
        <p className="section-sub">{t.specs.sub}</p>
        <div className="specs-grid">
          {t.specs.cards.map((s) => (
            <div className="spec-card" key={s.label}>
              <div className="val">{s.val}</div>
              <div className="label">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

const MEXICO_TZ = 'America/Mexico_City'
const APPT_TIME_SLOTS = ['09:00', '10:00', '11:00', '12:00', '13:00', '16:00', '17:00']

function isSameDay(a, b) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
}
function isWeekend(d) {
  const day = d.getDay()
  return day === 0 || day === 6
}
function isPastDay(d, today) {
  const dd = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const tt = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  return dd < tt
}
function toISODate(d) {
  return [d.getFullYear(), d.getMonth() + 1, d.getDate()].map((n) => String(n).padStart(2, '0')).join('-')
}
function formatSlotTime(hhmm, lang) {
  const [h, m] = hhmm.split(':').map(Number)
  const d = new Date(2000, 0, 1, h, m)
  return d.toLocaleTimeString(localeFor(lang), { hour: 'numeric', minute: '2-digit' })
}

function AppointmentPicker({ a, lang, selectedDate, selectedTime, onSelectDate, onSelectTime }) {
  const today = useMemo(() => new Date(), [])
  const [viewMonth, setViewMonth] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1))

  const currentMexicoTime = useMemo(() => (
    new Intl.DateTimeFormat(localeFor(lang), {
      timeZone: MEXICO_TZ,
      hour: 'numeric',
      minute: '2-digit',
    }).format(new Date())
  ), [lang])

  const weekdayLabels = useMemo(() => (
    Array.from({ length: 7 }, (_, i) => (
      new Intl.DateTimeFormat(localeFor(lang), { weekday: 'short' })
        .format(new Date(2024, 0, 1 + i))
    ))
  ), [lang])

  const monthLabel = new Intl.DateTimeFormat(localeFor(lang), { month: 'long', year: 'numeric' })
    .format(viewMonth)
  const isCurrentMonth = viewMonth.getFullYear() === today.getFullYear() && viewMonth.getMonth() === today.getMonth()

  const firstWeekday = (viewMonth.getDay() + 6) % 7
  const totalDays = new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 0).getDate()
  const cells = []
  for (let i = 0; i < firstWeekday; i++) cells.push(null)
  for (let d = 1; d <= totalDays; d++) cells.push(new Date(viewMonth.getFullYear(), viewMonth.getMonth(), d))
  while (cells.length % 7 !== 0) cells.push(null)

  return (
    <div className="appt-picker">
      <p className="appt-timezone">{a.timezoneNote} · {a.currentTime}: {currentMexicoTime}</p>

      <div className="appt-cal">
        <div className="appt-cal-nav">
          <button
            type="button"
            disabled={isCurrentMonth}
            onClick={() => setViewMonth((m) => new Date(m.getFullYear(), m.getMonth() - 1, 1))}
            aria-label="Previous month"
          >‹</button>
          <span>{monthLabel}</span>
          <button
            type="button"
            onClick={() => setViewMonth((m) => new Date(m.getFullYear(), m.getMonth() + 1, 1))}
            aria-label="Next month"
          >›</button>
        </div>
        <div className="appt-cal-weekdays">
          {weekdayLabels.map((w, i) => <span key={i}>{w}</span>)}
        </div>
        <div className="appt-cal-grid">
          {cells.map((d, i) => {
            if (!d) return <span key={i} className="appt-day empty" aria-hidden="true" />
            const disabled = isWeekend(d) || isPastDay(d, today)
            const selected = selectedDate && isSameDay(d, selectedDate)
            const isToday = isSameDay(d, today)
            return (
              <button
                type="button"
                key={i}
                className={`appt-day${selected ? ' selected' : ''}${isToday ? ' today' : ''}`}
                disabled={disabled}
                onClick={() => onSelectDate(d)}
              >
                {d.getDate()}
              </button>
            )
          })}
        </div>
      </div>

      {selectedDate && (
        <div className="appt-times">
          <p className="appt-times-label">{a.selectTime}</p>
          <div className="appt-times-grid">
            {APPT_TIME_SLOTS.map((slot) => (
              <button
                type="button"
                key={slot}
                className={`appt-time${selectedTime === slot ? ' selected' : ''}`}
                onClick={() => onSelectTime(slot)}
              >
                {formatSlotTime(slot, lang)}
              </button>
            ))}
          </div>
        </div>
      )}

      {selectedDate && selectedTime && (
        <p className="appt-summary">
          {a.summaryLabel}: {new Intl.DateTimeFormat(localeFor(lang), { weekday: 'long', day: 'numeric', month: 'long' }).format(selectedDate)}, {formatSlotTime(selectedTime, lang)} (CDMX)
        </p>
      )}
    </div>
  )
}

function Contact() {
  const { t, lang } = useLanguage()
  const [submitted, setSubmitted] = useState(false)
  const [stage, setStage] = useState('')
  const [mode, setMode] = useState('message')
  const [selectedDate, setSelectedDate] = useState(null)
  const [selectedTime, setSelectedTime] = useState(null)
  const [videoTool, setVideoTool] = useState('')
  const [attemptedSubmit, setAttemptedSubmit] = useState(false)
  const [sending, setSending] = useState(false)
  const [formError, setFormError] = useState('')
  const successRef = useRef(null)
  const f = t.contact.form
  const a = t.contact.appointment
  const stageHint = f.stageOptions.find((o) => o.label === stage)?.hint

  useEffect(() => {
    if (submitted) successRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [submitted])

  async function handleSubmit(e) {
    e.preventDefault()
    if (mode === 'schedule' && (!selectedDate || !selectedTime)) {
      setAttemptedSubmit(true)
      return
    }
    const els = e.currentTarget.elements
    const val = (id) => els.namedItem(id)?.value.trim() || undefined
    const body = {
      name: val('name'),
      company: val('company'),
      email: val('email'),
      country: val('country'),
      stage: stage || undefined,
      message: val('message'),
      lang,
      website: els.namedItem('website').value,
    }
    if (mode === 'schedule') {
      // Until live booking ships (specs/001-backend Story 2), staff confirm this slot by hand.
      body.preferred_slot = `${toISODate(selectedDate)} ${selectedTime}`
      body.video_tool = videoTool || undefined
    }
    setSending(true)
    setFormError('')
    try {
      await post('/contact', body)
      setSubmitted(true)
    } catch (err) {
      setFormError(errorMessage(err, t.formErrors))
    } finally {
      setSending(false)
    }
  }

  return (
    <section id="contact" className="contact-section">
      <div className="container contact-grid">
        <div className="contact-info">
          <span className="eyebrow">{t.contact.eyebrow}</span>
          <h2>{t.contact.title}</h2>
          <p>{t.contact.body}</p>
          <div className="info-row-pair">
            <div className="info-row">
              <span className="ico"><Icon name="mail" size={18} /></span>
              <div>
                <div className="t">{t.contact.emailLabel}</div>
                <div className="d">{t.contact.email}</div>
              </div>
            </div>
            <a className="info-row" href="https://wa.me/526462416056" target="_blank" rel="noopener noreferrer">
              <span className="ico"><Icon name="whatsapp" size={18} /></span>
              <div>
                <div className="t">{t.contact.whatsappLabel}</div>
                <div className="d">{t.contact.whatsapp}</div>
              </div>
            </a>
          </div>
          <div className="info-row">
            <span className="ico"><Icon name="pin" size={18} /></span>
            <div>
              <div className="t">{t.contact.locationLabel}</div>
              <div className="d">{t.contact.location}</div>
            </div>
          </div>
        </div>

        {submitted ? (
          <div className="form-success" ref={successRef}>
            {mode === 'schedule' ? t.contact.successSchedule : t.contact.success}
          </div>
        ) : (
          <form className="lead-form" onSubmit={handleSubmit}>
            <div className="mode-toggle" role="group">
              <button
                type="button"
                className={mode === 'message' ? 'active' : ''}
                onClick={() => setMode('message')}
              >
                {a.modeMessage}
              </button>
              <button
                type="button"
                className={mode === 'schedule' ? 'active' : ''}
                onClick={() => setMode('schedule')}
              >
                {a.modeSchedule}
              </button>
            </div>

            <div className="form-two">
              <div className="form-row">
                <label htmlFor="name">{f.name}</label>
                <input id="name" type="text" placeholder={f.namePlaceholder} required />
              </div>
              <div className="form-row">
                <label htmlFor="company">{f.company}</label>
                <input id="company" type="text" placeholder={f.companyPlaceholder} required />
              </div>
            </div>
            <div className="form-two">
              <div className="form-row">
                <label htmlFor="email">{f.email}</label>
                <input id="email" type="email" placeholder={f.emailPlaceholder} required />
              </div>
              <div className="form-row">
                <label htmlFor="country">{f.country}</label>
                <select id="country" defaultValue="">
                  <option value="" disabled>{f.countryPlaceholder}</option>
                  {f.countries.map((g) => (
                    g.group ? (
                      <optgroup key={g.group} label={g.group}>
                        {g.options.map((o) => <option key={o}>{o}</option>)}
                      </optgroup>
                    ) : (
                      g.options.map((o) => <option key={o}>{o}</option>)
                    )
                  ))}
                </select>
              </div>
            </div>
            <div className="form-row">
              <label htmlFor="stage">{f.stage}</label>
              <select id="stage" value={stage} onChange={(e) => setStage(e.target.value)}>
                <option value="" disabled>{f.stagePlaceholder}</option>
                {f.stageOptions.map((o) => (
                  <option key={o.label} value={o.label}>{o.label}</option>
                ))}
              </select>
              {stageHint && <p className="field-hint">{stageHint}</p>}
            </div>

            {mode === 'schedule' && (
              <div className="form-row">
                <label>{a.selectDate}</label>
                <AppointmentPicker
                  a={a}
                  lang={lang}
                  selectedDate={selectedDate}
                  selectedTime={selectedTime}
                  onSelectDate={(d) => { setSelectedDate(d); setSelectedTime(null) }}
                  onSelectTime={setSelectedTime}
                />
                {attemptedSubmit && (!selectedDate || !selectedTime) && (
                  <p className="field-error">{a.required}</p>
                )}
              </div>
            )}

            {mode === 'schedule' && (
              <div className="form-row">
                <label htmlFor="videoTool">{a.videoTool}</label>
                <select id="videoTool" value={videoTool} onChange={(e) => setVideoTool(e.target.value)}>
                  <option value="" disabled>{a.videoToolPlaceholder}</option>
                  {a.videoToolOptions.map((o) => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
              </div>
            )}

            <div className="form-row">
              <label htmlFor="message">{f.message}</label>
              <textarea id="message" rows="4" placeholder={f.messagePlaceholder} />
            </div>

            <details className="privacy-details">
              <summary>{t.contact.privacy.title}</summary>
              <p>{t.contact.privacy.summary}</p>
              <ul>
                {t.contact.privacy.points.map((p) => <li key={p}>{p}</li>)}
              </ul>
            </details>

            <label className="consent-row">
              <input
                type="checkbox"
                required
                onInvalid={(e) => e.target.setCustomValidity(t.contact.privacy.consentRequired)}
                onChange={(e) => e.target.setCustomValidity('')}
              />
              <span>{t.contact.privacy.consentLabel}</span>
            </label>

            {/* Honeypot: hidden from people and assistive tech; bots that fill it are ignored. */}
            <div className="hp-field" aria-hidden="true">
              <label htmlFor="website">Website</label>
              <input id="website" type="text" tabIndex={-1} autoComplete="off" defaultValue="" />
            </div>

            {formError && <p className="field-error" role="alert">{formError}</p>}

            <button type="submit" className="btn btn-dark" style={{ width: '100%' }} disabled={sending}>
              {sending ? t.formErrors.sending : f.submit}
            </button>
          </form>
        )}
      </div>
    </section>
  )
}

function MadeInMexicoBadge() {
  return (
    <div className="mim-badge" role="img" aria-label="Hecho en México">
      <span className="mim-top">HECHO EN</span>
      <span className="mim-mx">MÉXICO</span>
      <span className="mim-flag" aria-hidden="true"><i /><i /><i /></span>
    </div>
  )
}

function Footer() {
  const { t } = useLanguage()
  return (
    <footer className="site-footer">
      <div className="container">
        <div className="footer-grid">
          <div className="footer-brand">
            <a href="#" className="logo">
              <span className="logo-mark" aria-hidden="true" />
              VeritX Vision
            </a>
            <p>{t.footer.tagline}</p>
            <div className="footer-social">
              <span className="footer-social-icon" title="LinkedIn" aria-label="LinkedIn">
                <Icon name="linkedin" size={18} />
              </span>
            </div>
            <MadeInMexicoBadge />
          </div>
          <div className="footer-cols">
            <div className="footer-col">
              <h5>{t.footer.product}</h5>
              {t.footer.productLinks.map((l) => (
                <a key={l.href} href={l.href}>{l.label}</a>
              ))}
            </div>
            <div className="footer-col">
              <h5>{t.footer.company}</h5>
              <a href="#/about">{t.footer.about}</a>
              <a href="#contact">{t.footer.contact}</a>
            </div>
            <div className="footer-col">
              <h5>{t.footer.legal}</h5>
              <a href="#/privacy">{t.footer.privacy}</a>
              <span>{t.footer.terms}</span>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <span>© {new Date().getFullYear()} VeritX Vision. {t.footer.rights}</span>
        </div>
      </div>
    </footer>
  )
}

function Site() {
  const route = useRoute()

  useEffect(() => {
    if (SATELLITE_ROUTES.includes(route)) {
      window.scrollTo(0, 0)
    } else {
      const hash = window.location.hash
      if (hash && !hash.startsWith('#/')) {
        document.getElementById(hash.slice(1))?.scrollIntoView()
      }
    }
  }, [route])

  return (
    <>
      <Header />
      {route === 'demo' && <DemoPage />}
      {route === 'calculator' && <CalculatorPage />}
      {route === 'about' && <AboutPage />}
      {route === 'privacy' && <PrivacyPolicyPage />}
      {route === 'login' && <LoginPage />}
      {route === 'register' && <RegisterPage />}
      {route === 'verify-email' && <VerifyEmailPage />}
      {route === 'forgot-password' && <ForgotPasswordPage />}
      {route === 'recover-username' && <RecoverUsernamePage />}
      {route === 'vision-home' && <VisionHomePage />}
      {route === 'home' && (
        <>
          <Hero />
          <VisionA />
          <HowItWorks />
          <UseCases />
          <Comparison />
          <Specs />
          <Contact />
        </>
      )}
      <Footer />
    </>
  )
}

export default function App() {
  return (
    <LanguageProvider>
      <Site />
    </LanguageProvider>
  )
}
