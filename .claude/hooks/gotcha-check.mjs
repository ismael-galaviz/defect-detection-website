// SessionStart hook: checks GOTCHA.md so a stale or malformed entry is flagged at the start of a
// session instead of lingering. Only warns — it never blocks a session, and prints nothing when
// every entry is complete and in date.
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

const REQUIRED = ['Added', 'Review by', 'Remove when']
const DATE = /^\d{4}-\d{2}-\d{2}$/

const root = process.env.CLAUDE_PROJECT_DIR || process.cwd()
const file = join(root, 'GOTCHA.md')
if (!existsSync(file)) process.exit(0)

// Local date, so "past its Review by" matches the owner's calendar rather than UTC.
const now = new Date()
const today = [now.getFullYear(), now.getMonth() + 1, now.getDate()]
  .map((n) => String(n).padStart(2, '0'))
  .join('-')

// Entries are the `## ` sections; fenced blocks (the format example) are skipped.
const entries = []
let fenced = false
for (const line of readFileSync(file, 'utf8').split('\n')) {
  if (line.startsWith('```')) fenced = !fenced
  if (fenced) continue
  if (line.startsWith('## ')) entries.push({ title: line.slice(3).trim(), fields: {} })
  const field = line.match(/^- ([A-Za-z ]+):\s*(.*)$/)
  if (field && entries.length) entries.at(-1).fields[field[1].trim()] = field[2].trim()
}

const problems = []
for (const { title, fields } of entries) {
  const missing = REQUIRED.filter((k) => !fields[k])
  if (missing.length) problems.push(`"${title}" is missing: ${missing.join(', ')}`)
  for (const k of ['Added', 'Review by']) {
    if (fields[k] && !DATE.test(fields[k])) problems.push(`"${title}" has a bad ${k} date (YYYY-MM-DD)`)
  }
  const review = fields['Review by']
  if (review && DATE.test(review) && review <= today) {
    problems.push(`"${title}" was due for review on ${review}; remove when: ${fields['Remove when'] || '?'}`)
  }
}

if (problems.length) {
  const text =
    'GOTCHA.md needs attention — tell the owner, then resolve and delete each entry or renew its ' +
    'Review by date with a reason:\n- ' +
    problems.join('\n- ')
  process.stdout.write(
    JSON.stringify({ hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext: text } }),
  )
}
