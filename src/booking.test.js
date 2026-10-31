import { describe, expect, it } from 'vitest'
import { groupSlotsByDate, toISODate } from './booking.js'

describe('booking helpers', () => {
  it('groups CDMX slots by date without timezone conversion', () => {
    const slots = ['2026-11-04T09:00:00-06:00', '2026-11-04T16:00:00-06:00', '2026-11-05T17:00:00-06:00']
    expect(groupSlotsByDate(slots)).toEqual({
      '2026-11-04': [{ time: '09:00', iso: slots[0] }, { time: '16:00', iso: slots[1] }],
      '2026-11-05': [{ time: '17:00', iso: slots[2] }],
    })
  })

  it('formats calendar days with zero padding', () => {
    expect(toISODate(new Date(2026, 0, 5))).toBe('2026-01-05')
  })
})
