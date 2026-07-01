import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { formatRelative, stalenessTier } from './staleness'

const NOW = new Date('2026-07-01T00:00:00.000Z')

function daysAgo(days: number): string {
  return new Date(NOW.getTime() - days * 86_400_000).toISOString()
}

beforeEach(() => {
  vi.useFakeTimers()
  vi.setSystemTime(NOW)
})

afterEach(() => {
  vi.useRealTimers()
})

describe('stalenessTier', () => {
  it('returns none for null', () => {
    expect(stalenessTier(null)).toBe('none')
  })

  it('returns none for an unparsable date', () => {
    expect(stalenessTier('not-a-date')).toBe('none')
  })

  it('returns fresh at exactly the aging boundary (45d)', () => {
    expect(stalenessTier(daysAgo(45))).toBe('fresh')
  })

  it('returns fresh just under the aging boundary', () => {
    expect(stalenessTier(daysAgo(10))).toBe('fresh')
  })

  it('returns aging just past the aging boundary', () => {
    expect(stalenessTier(daysAgo(45.5))).toBe('aging')
  })

  it('returns aging at exactly the stale boundary (90d)', () => {
    expect(stalenessTier(daysAgo(90))).toBe('aging')
  })

  it('returns stale just past the stale boundary', () => {
    expect(stalenessTier(daysAgo(90.5))).toBe('stale')
  })

  it('returns stale well past the stale boundary', () => {
    expect(stalenessTier(daysAgo(365))).toBe('stale')
  })
})

describe('formatRelative', () => {
  it('returns em dash for null', () => {
    expect(formatRelative(null)).toBe('—')
  })

  it('returns em dash for an unparsable date', () => {
    expect(formatRelative('not-a-date')).toBe('—')
  })

  it('returns "just now" for under an hour ago', () => {
    expect(
      formatRelative(new Date(NOW.getTime() - 30 * 1000).toISOString()),
    ).toBe('just now')
  })

  it('returns hours ago for under a day', () => {
    expect(
      formatRelative(new Date(NOW.getTime() - 5 * 3600 * 1000).toISOString()),
    ).toBe('5h ago')
  })

  it('returns days ago for under a month', () => {
    expect(formatRelative(daysAgo(3))).toBe('3d ago')
  })

  it('returns months ago for under a year', () => {
    expect(formatRelative(daysAgo(60))).toBe('2mo ago')
  })

  it('returns years ago for a year or more', () => {
    expect(formatRelative(daysAgo(400))).toBe('1y ago')
  })
})
