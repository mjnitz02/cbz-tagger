export const STALE_DAYS = { aging: 45, stale: 90 } as const

export type StalenessTier = 'fresh' | 'aging' | 'stale' | 'none'

export function stalenessTier(iso: string | null): StalenessTier {
  if (!iso) return 'none'
  const ts = Date.parse(iso)
  if (Number.isNaN(ts)) return 'none'
  const ageDays = (Date.now() - ts) / 86_400_000
  if (ageDays <= STALE_DAYS.aging) return 'fresh'
  if (ageDays <= STALE_DAYS.stale) return 'aging'
  return 'stale'
}

export function formatRelative(iso: string | null): string {
  if (!iso) return '—'
  const ts = Date.parse(iso)
  if (Number.isNaN(ts)) return '—'
  const sec = Math.max(0, (Date.now() - ts) / 1000)
  const days = sec / 86_400
  if (days < 1) {
    const h = sec / 3600
    return h < 1 ? 'just now' : `${Math.floor(h)}h ago`
  }
  if (days < 30) return `${Math.floor(days)}d ago`
  if (days < 365) return `${Math.floor(days / 30)}mo ago`
  return `${Math.floor(days / 365)}y ago`
}
