// Thin client for the backend (server/, reached same-origin at /api — see docs/deployment).
// Every failure is thrown as ApiError with a machine-readable `error` code from
// specs/001-backend/contracts/api.md ('network' when the request never got an answer).

export class ApiError extends Error {
  constructor(status, error, fields = {}) {
    super(error)
    this.status = status
    this.error = error
    this.fields = fields
  }
}

async function request(method, path, body) {
  let res
  try {
    res = await fetch(`/api${path}`, {
      method,
      credentials: 'same-origin',
      headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, 'network')
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = new ApiError(res.status, data.error || 'server_error', data.fields || {})
    if (data.retry_after) err.retry_after = data.retry_after
    throw err
  }
  return data
}

export const get = (path) => request('GET', path)
export const post = (path, body = {}) => request('POST', path, body)

// Maps an ApiError to one of the shared form-error messages in translations.js → formErrors.
export function errorMessage(err, formErrors) {
  if (err?.error === 'rate_limited') return formErrors.rateLimited
  if (err?.error === 'invalid') return formErrors.invalid
  return formErrors.network
}

// Multipart upload of one file (field "file"); the browser sets the multipart boundary.
export async function upload(path, file) {
  const body = new FormData()
  body.append('file', file)
  let res
  try {
    res = await fetch(`/api${path}`, { method: 'POST', credentials: 'same-origin', body })
  } catch {
    throw new ApiError(0, 'network')
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new ApiError(res.status, data.error || 'server_error', data.fields || {})
  return data
}
