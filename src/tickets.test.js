import { describe, expect, it } from 'vitest'
import { fileProblem, MAX_BYTES } from './tickets.js'

const f = (name, type, size = 10) => ({ name, type, size })

describe('fileProblem', () => {
  it('accepts up to 3 small PNG/JPEG/PDF files', () => {
    expect(fileProblem([f('a.png', 'image/png'), f('b.jpg', 'image/jpeg'), f('c.pdf', 'application/pdf')])).toBe(null)
    expect(fileProblem([])).toBe(null)
  })
  it('rejects too many, wrong type, too large', () => {
    expect(fileProblem([1, 2, 3, 4].map((i) => f(`${i}.png`, 'image/png')))).toEqual({ key: 'tooMany' })
    expect(fileProblem([f('x.exe', 'application/x-msdownload')])).toEqual({ key: 'unsupportedType', file: 'x.exe' })
    expect(fileProblem([f('big.png', 'image/png', MAX_BYTES + 1)])).toEqual({ key: 'tooLarge', file: 'big.png' })
  })
})
