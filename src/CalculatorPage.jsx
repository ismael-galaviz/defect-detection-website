import { useMemo, useState } from 'react'
import { useLanguage, localeFor } from './i18n.jsx'
import { Icon } from './icons.jsx'
import { errorMessage, post } from './api.js'

// Defaults mirror the worked examples from the source ROI guide (Guia_Ingeniero_Calidad_ROI.docx),
// except lineSpeed — see the note on CALC.lineSpeed below for why that one was redesigned.
export const DEFAULTS = {
  defects: { rateBefore: 1.2, rateAfter: 0.2, volume: 500000, costPerDefect: 150 },
  laborHours: { hoursBefore: 12, hoursAfter: 2, hourlyCost: 80, shiftsPerYear: 250 },
  lineSpeed: { speedBefore: 70, speedAfter: 100, hoursPerYear: 4000, marginPerMeter: 0.5 },
}

export const CALC = {
  defects: (v) => Math.max(0, v.rateBefore - v.rateAfter) / 100 * v.volume * v.costPerDefect,
  laborHours: (v) => Math.max(0, v.hoursBefore - v.hoursAfter) * v.hourlyCost * v.shiftsPerYear,
  // Speed is m/min, so extra meters/year needs a min→hour conversion (×60) before it can be
  // multiplied by hours/year — the original formula (ported from the source guide) skipped that
  // conversion, which is a real unit-consistency bug, not just a mismatch with the guide's example
  // number. Also collapses "units produced per meter" × "margin per unit" into a single
  // "margin per meter produced" input: one fewer error-prone hop, and it matches the m²-based
  // framing already used in the defect-reduction section instead of introducing an unrelated
  // "unit" concept.
  lineSpeed: (v) => Math.max(0, v.speedAfter - v.speedBefore) * 60 * v.hoursPerYear * v.marginPerMeter,
}

const MONEY_FIELD_KEYS = new Set(['costPerDefect', 'hourlyCost', 'marginPerMeter'])

function formatCurrency(n, lang, currency) {
  return new Intl.NumberFormat(localeFor(lang), {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(Math.round(n) || 0)
}

// Shows thousand separators while at rest; switches to raw digits while focused so typing/cursor
// position isn't disturbed by live comma insertion.
function CalcNumberInput({ id, value, onChange }) {
  const { lang } = useLanguage()
  const [focused, setFocused] = useState(false)

  const display = focused
    ? String(value)
    : value === '' || value === null || value === undefined
      ? ''
      : Number(value).toLocaleString(localeFor(lang), { maximumFractionDigits: 4 })

  return (
    <input
      id={id}
      type="text"
      inputMode="decimal"
      value={display}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      onChange={(e) => {
        const raw = e.target.value.replace(/,/g, '')
        if (raw === '' || /^\d*\.?\d*$/.test(raw)) onChange(raw)
      }}
    />
  )
}

function CalcSection({ section, values, onFieldChange, result, resultLabel, formulaLabel, currency }) {
  return (
    <div className="calc-section">
      <div className="calc-section-header">
        <div className="calc-section-icon"><Icon name={section.icon} /></div>
        <div>
          <h3>{section.title}</h3>
          <p>{section.body}</p>
        </div>
      </div>

      <details className="calc-formula">
        <summary>{formulaLabel}</summary>
        <pre>{section.formula}</pre>
      </details>

      <div className="calc-fields">
        {section.fields.map((f) => (
          <div className="form-row" key={f.key}>
            <label htmlFor={`${section.id}-${f.key}`}>
              {f.label}{MONEY_FIELD_KEYS.has(f.key) ? ` (${currency})` : ''}
            </label>
            <CalcNumberInput
              id={`${section.id}-${f.key}`}
              value={values[f.key]}
              onChange={(val) => onFieldChange(f.key, val)}
            />
          </div>
        ))}
      </div>

      <div className="calc-result">
        <span>{resultLabel}</span>
        <strong>{result}</strong>
      </div>

      <p className="calc-hint">{section.hint}</p>
    </div>
  )
}

export default function CalculatorPage() {
  const { t, lang } = useLanguage()
  const c = t.calculatorPage
  const [values, setValues] = useState(() => JSON.parse(JSON.stringify(DEFAULTS)))
  const [currency, setCurrency] = useState('MXN')
  const [sendName, setSendName] = useState('')
  const [sendEmail, setSendEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState('')

  function handleFieldChange(sectionId, key, val) {
    setValues((v) => ({ ...v, [sectionId]: { ...v[sectionId], [key]: val } }))
  }

  const results = useMemo(() => {
    const out = {}
    for (const s of c.sections) {
      const safe = Object.fromEntries(
        Object.entries(values[s.id]).map(([k, n]) => [k, Number(n) || 0])
      )
      out[s.id] = CALC[s.id](safe)
    }
    return out
  }, [values, c.sections])

  const totalAnnual = Object.values(results).reduce((a, b) => a + b, 0)

  async function handleSendResults(e) {
    e.preventDefault()
    const inputs = Object.fromEntries(Object.entries(values).map(([id, fields]) => [
      id, Object.fromEntries(Object.entries(fields).map(([k, n]) => [k, Number(n) || 0])),
    ]))
    setSending(true)
    setSendError('')
    try {
      await post('/calculator-results', {
        name: sendName.trim() || undefined,
        email: sendEmail.trim(),
        lang,
        currency,
        inputs,
        results: { ...results, total: totalAnnual },
        website: e.currentTarget.elements.namedItem('calc-website').value,
      })
      setSent(true)
    } catch (err) {
      setSendError(errorMessage(err, t.formErrors))
    } finally {
      setSending(false)
    }
  }

  return (
    <main>
      <section className="demo-hero">
        <div className="container">
          <span className="eyebrow">{c.eyebrow}</span>
          <h1>{c.title}</h1>
          <p className="lead">{c.intro}</p>
        </div>
      </section>

      <section className="demo-section">
        <div className="container">
          <div className="calc-currency">
            <div className="form-row">
              <label htmlFor="calc-currency">{c.currencyLabel}</label>
              <select id="calc-currency" value={currency} onChange={(e) => setCurrency(e.target.value)}>
                {c.currencyOptions.map((g) => (
                  g.group ? (
                    <optgroup key={g.group} label={g.group}>
                      {g.options.map((o) => <option key={o.code} value={o.code}>{o.label}</option>)}
                    </optgroup>
                  ) : (
                    g.options.map((o) => <option key={o.code} value={o.code}>{o.label}</option>)
                  )
                ))}
              </select>
            </div>
            <p className="field-hint">{c.currencyHint}</p>
          </div>

          {c.sections.map((s) => (
            <CalcSection
              key={s.id}
              section={s}
              values={values[s.id]}
              onFieldChange={(key, val) => handleFieldChange(s.id, key, val)}
              result={formatCurrency(results[s.id], lang, currency)}
              resultLabel={c.resultLabel}
              formulaLabel={c.formulaLabel}
              currency={currency}
            />
          ))}

          <div className="calc-total">
            <h3>{c.totalTitle}</h3>
            <div className="calc-total-row calc-payback">
              <span>{c.totalAnnual}</span>
              <strong>{formatCurrency(totalAnnual, lang, currency)}</strong>
            </div>
            <p className="calc-methodology">{c.methodologyNote}</p>
          </div>

          <div className="calc-send">
            <h3>{c.sendResults.title}</h3>
            <p>{c.sendResults.body}</p>
            {sent ? (
              <p className="field-hint">{c.sendResults.success}</p>
            ) : (
              <>
              <form className="calc-send-form" onSubmit={handleSendResults}>
                <input
                  type="text"
                  value={sendName}
                  onChange={(e) => setSendName(e.target.value)}
                  placeholder={c.sendResults.namePlaceholder}
                  aria-label={c.sendResults.name}
                  required
                />
                <input
                  type="email"
                  value={sendEmail}
                  onChange={(e) => setSendEmail(e.target.value)}
                  placeholder={c.sendResults.emailPlaceholder}
                  aria-label={c.sendResults.email}
                  required
                />
                <div className="hp-field" aria-hidden="true">
                  <label htmlFor="calc-website">Website</label>
                  <input id="calc-website" type="text" tabIndex={-1} autoComplete="off" defaultValue="" />
                </div>
                <button type="submit" className="btn btn-outline" disabled={sending}>
                  {sending ? t.formErrors.sending : c.sendResults.submit}
                </button>
              </form>
              {sendError && <p className="field-error" role="alert">{sendError}</p>}
              </>
            )}
          </div>

          <div className="calc-soft">
            <h3>{c.softSavings.title}</h3>
            <p>{c.softSavings.intro}</p>
            <div className="usecases-grid why-grid">
              {c.softSavings.items.map((item) => (
                <div className="usecase-card" key={item.title}>
                  <div className="usecase-icon"><Icon name={item.icon} /></div>
                  <h4>{item.title}</h4>
                  <p>{item.body}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="calc-cta">
            <p>{c.ctaSub}</p>
            <a href="#contact" className="btn btn-primary">{c.cta}</a>
          </div>
        </div>
      </section>
    </main>
  )
}
