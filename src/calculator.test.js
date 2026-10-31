import { describe, expect, it } from 'vitest'
import { CALC, DEFAULTS } from './CalculatorPage.jsx'

describe('ROI calculator formulas', () => {
  it('matches the documented defaults (SDD §10.16)', () => {
    expect(CALC.defects(DEFAULTS.defects)).toBe(750000)
    expect(CALC.laborHours(DEFAULTS.laborHours)).toBe(200000)
    expect(CALC.lineSpeed(DEFAULTS.lineSpeed)).toBe(3600000)
  })

  it('converts m/min to m/hour in the line-speed formula', () => {
    const v = { speedBefore: 0, speedAfter: 1, hoursPerYear: 1, marginPerMeter: 1 }
    expect(CALC.lineSpeed(v)).toBe(60)
  })

  it('never reports negative savings when "after" is worse than "before"', () => {
    expect(CALC.defects({ ...DEFAULTS.defects, rateAfter: 5 })).toBe(0)
    expect(CALC.laborHours({ ...DEFAULTS.laborHours, hoursAfter: 20 })).toBe(0)
    expect(CALC.lineSpeed({ ...DEFAULTS.lineSpeed, speedAfter: 10 })).toBe(0)
  })
})
