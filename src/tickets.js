// Client-side pre-checks for ticket attachments; the server re-checks by file content
// (server/app/uploads.py), so these only give instant feedback.

export const MAX_FILES = 3
export const MAX_BYTES = 2 * 1024 * 1024
export const ACCEPT = ['image/png', 'image/jpeg', 'application/pdf']

// → null, or { key: 'tooMany'|'tooLarge'|'unsupportedType', file? }
export function fileProblem(files) {
  if (files.length > MAX_FILES) return { key: 'tooMany' }
  for (const f of files) {
    if (!ACCEPT.includes(f.type)) return { key: 'unsupportedType', file: f.name }
    if (f.size > MAX_BYTES) return { key: 'tooLarge', file: f.name }
  }
  return null
}
