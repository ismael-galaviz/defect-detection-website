// Helpers for the meeting picker (contact form). Slots come from /api/availability.

export const BOOKING_DAYS_AHEAD = 60 // matches the backend's window (server/app/booking.py)

// Calendar-cell date → 'YYYY-MM-DD' (the picker's dates are calendar days, not instants).
export function toISODate(d) {
  return [d.getFullYear(), d.getMonth() + 1, d.getDate()].map((n) => String(n).padStart(2, '0')).join('-')
}

// Slots arrive as ISO strings already in CDMX ('2026-11-04T10:00:00-06:00'), so date and time
// are read off the string with no timezone math in the visitor's browser.
export function groupSlotsByDate(isoSlots) {
  const byDate = {}
  for (const iso of isoSlots) (byDate[iso.slice(0, 10)] ||= []).push({ time: iso.slice(11, 16), iso })
  return byDate
}
