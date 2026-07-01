import { Fragment, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertDialog } from 'radix-ui'
import { ChevronDown, ChevronRight, RotateCw, Trash2 } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { apiClient } from '@/lib/api-client'
import { cn } from '@/lib/utils'
import { formatRelative, stalenessTier } from '@/lib/staleness'
import type { components } from '@/lib/api-schema'

type SeriesStateItem = components['schemas']['SeriesStateItem']
type SortMode = 'name' | 'recent' | 'stalest'
type TrackedFilter = 'all' | 'tracked' | 'untracked'

const BUSY_MESSAGE = 'Scanner is busy. Please wait and try again.'

const CANONICAL_STATUSES = [
  'ongoing',
  'hiatus',
  'completed',
  'cancelled',
  'dropped',
]

const STATUS_BADGES: Record<string, { label: string; className: string }> = {
  ongoing: { label: 'Ongoing', className: 'bg-green-500/15 text-green-400' },
  hiatus: { label: 'Hiatus', className: 'bg-amber-500/15 text-amber-400' },
  completed: { label: 'Completed', className: 'bg-blue-500/15 text-blue-400' },
  cancelled: { label: 'Cancelled', className: 'bg-red-500/15 text-red-400' },
  dropped: { label: 'Dropped', className: 'bg-zinc-500/15 text-zinc-400' },
}

const STATUS_FALLBACK = 'bg-zinc-500/15 text-zinc-400'

const ACCENT_CLASS: Record<ReturnType<typeof stalenessTier>, string> = {
  fresh: 'border-l-4 border-green-500',
  aging: 'border-l-4 border-amber-500',
  stale: 'border-l-4 border-red-500',
  none: 'border-l-4 border-transparent',
}

function StatusBadge({ status }: { status: string }) {
  const badge = STATUS_BADGES[status] ?? {
    label: status.charAt(0).toUpperCase() + status.slice(1),
    className: STATUS_FALLBACK,
  }
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        badge.className,
      )}
    >
      {badge.label}
    </span>
  )
}

function TrackedBadge({ tracked }: { tracked: boolean }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
        tracked
          ? 'bg-green-500/15 text-green-400'
          : 'bg-zinc-500/15 text-zinc-400',
      )}
    >
      <span
        className={cn(
          'size-1.5 rounded-full',
          tracked ? 'bg-green-400' : 'bg-zinc-500',
        )}
      />
      {tracked ? 'Tracked' : 'Untracked'}
    </span>
  )
}

function isAttention(row: SeriesStateItem): boolean {
  if (row.status !== 'ongoing' && row.status !== 'hiatus') return false
  return (
    row.latest_chapter_date === null ||
    stalenessTier(row.latest_chapter_date) === 'stale'
  )
}

function byName(a: SeriesStateItem, b: SeriesStateItem) {
  return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })
}

function sortSeries(
  rows: SeriesStateItem[],
  mode: SortMode,
): SeriesStateItem[] {
  const arr = [...rows]
  if (mode === 'name') {
    arr.sort(byName)
    return arr
  }
  const direction = mode === 'recent' ? -1 : 1
  arr.sort((a, b) => {
    if (a.latest_chapter_date === null && b.latest_chapter_date === null) {
      return byName(a, b)
    }
    if (a.latest_chapter_date === null) return mode === 'recent' ? 1 : -1
    if (b.latest_chapter_date === null) return mode === 'recent' ? -1 : 1
    const diff =
      direction *
      (Date.parse(a.latest_chapter_date) - Date.parse(b.latest_chapter_date))
    return diff !== 0 ? diff : byName(a, b)
  })
  return arr
}

function SeriesPage() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<Set<string>>(new Set())
  const [trackedFilter, setTrackedFilter] = useState<TrackedFilter>('all')
  const [pluginFilter, setPluginFilter] = useState<string>('all')
  const [needsAttentionOnly, setNeedsAttentionOnly] = useState(false)
  const [sortMode, setSortMode] = useState<SortMode>('name')
  const [openId, setOpenId] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<SeriesStateItem | null>(null)
  const [statusMessage, setStatusMessage] = useState<string>()

  const { data, isLoading, error } = useQuery({
    queryKey: ['series-state'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/scanner/state')
      if (error) throw error
      return data
    },
    refetchInterval: 60_000,
  })

  const queryClient = useQueryClient()

  const { data: scannerStatus } = useQuery({
    queryKey: ['scanner-status'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/scanner/status')
      if (error) throw error
      return data
    },
    refetchInterval: 5_000,
  })

  const refresh = useMutation({
    mutationFn: async () => {
      const { error, response } = await apiClient.POST('/api/scanner/refresh')
      const status = response.status
      if (error) {
        throw new Error(
          status === 409
            ? 'A scan is already running. Try again shortly.'
            : 'Database refresh failed. Check the logs.',
        )
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['series-state'] })
      queryClient.invalidateQueries({ queryKey: ['scanner-status'] })
    },
  })

  const deleteSeries = useMutation({
    mutationFn: async (target: SeriesStateItem) => {
      const { response } = await apiClient.DELETE(
        '/api/scanner/series/{entity_id}',
        {
          params: {
            path: { entity_id: target.entity_id },
            query: { entity_name: target.name },
          },
        },
      )
      return response
    },
    onSuccess: (response, target) => {
      if (response.status === 409) {
        setStatusMessage(BUSY_MESSAGE)
        return
      }
      setStatusMessage(`Removed ${target.name} from the database`)
      setDeleteTarget(null)
      queryClient.invalidateQueries({ queryKey: ['series-state'] })
    },
  })

  const refreshing = refresh.isPending || (scannerStatus?.busy ?? false)

  const series = useMemo(() => data?.series ?? [], [data])

  const statusOptions = useMemo(() => {
    const present = new Set(series.map((row) => row.status))
    const extra = [...present]
      .filter((status) => !CANONICAL_STATUSES.includes(status))
      .sort()
    return [...CANONICAL_STATUSES, ...extra]
  }, [series])

  const pluginOptions = useMemo(() => {
    return [...new Set(series.map((row) => row.plugin))].sort()
  }, [series])

  const visibleSeries = useMemo(() => {
    const searchTerm = search.toLowerCase().trim()
    const filtered = series.filter((row) => {
      const matchesSearch =
        searchTerm === '' || row.name.toLowerCase().includes(searchTerm)
      const matchesStatus =
        statusFilter.size === 0 || statusFilter.has(row.status)
      const matchesTracked =
        trackedFilter === 'all' ||
        (trackedFilter === 'tracked' ? row.tracked : !row.tracked)
      const matchesPlugin =
        pluginFilter === 'all' || row.plugin === pluginFilter
      const matchesAttention = !needsAttentionOnly || isAttention(row)
      return (
        matchesSearch &&
        matchesStatus &&
        matchesTracked &&
        matchesPlugin &&
        matchesAttention
      )
    })
    return sortSeries(filtered, sortMode)
  }, [
    series,
    search,
    statusFilter,
    trackedFilter,
    pluginFilter,
    needsAttentionOnly,
    sortMode,
  ])

  function toggleStatus(status: string) {
    setStatusFilter((prev) => {
      const next = new Set(prev)
      if (next.has(status)) {
        next.delete(status)
      } else {
        next.add(status)
      }
      return next
    })
  }

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex items-start justify-between gap-4">
        <h1 className="text-2xl font-medium">Series</h1>
        <div className="flex flex-col items-end gap-1">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => refresh.mutate()}
            disabled={refreshing}
          >
            <RotateCw className={cn('size-4', refreshing && 'animate-spin')} />
            {refreshing ? 'Refreshing…' : 'Refresh database'}
          </Button>
          {refresh.isError && (
            <span className="text-xs text-destructive">
              {(refresh.error as Error).message}
            </span>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="series-search"
            className="text-xs text-muted-foreground"
          >
            Search
          </label>
          <Input
            id="series-search"
            placeholder="Search by name"
            className="w-56"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <span className="text-xs text-muted-foreground">Status</span>
          <div className="flex flex-wrap gap-1">
            {statusOptions.map((status) => {
              const active = statusFilter.has(status)
              const badge = STATUS_BADGES[status]
              return (
                <Button
                  key={status}
                  type="button"
                  size="sm"
                  variant={active ? 'secondary' : 'outline'}
                  aria-pressed={active}
                  onClick={() => toggleStatus(status)}
                >
                  {badge?.label ??
                    status.charAt(0).toUpperCase() + status.slice(1)}
                </Button>
              )
            })}
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="tracked-filter"
            className="text-xs text-muted-foreground"
          >
            Tracked
          </label>
          <Select
            value={trackedFilter}
            onValueChange={(value) => setTrackedFilter(value as TrackedFilter)}
          >
            <SelectTrigger id="tracked-filter" className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="tracked">Tracked</SelectItem>
              <SelectItem value="untracked">Untracked</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="plugin-filter"
            className="text-xs text-muted-foreground"
          >
            Plugin
          </label>
          <Select value={pluginFilter} onValueChange={setPluginFilter}>
            <SelectTrigger id="plugin-filter" className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              {pluginOptions.map((plugin) => (
                <SelectItem key={plugin} value={plugin}>
                  {plugin}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="sort-mode" className="text-xs text-muted-foreground">
            Sort
          </label>
          <Select
            value={sortMode}
            onValueChange={(value) => setSortMode(value as SortMode)}
          >
            <SelectTrigger id="sort-mode" className="w-44">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="name">Name A-Z</SelectItem>
              <SelectItem value="recent">Recently updated</SelectItem>
              <SelectItem value="stalest">Stalest first</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <label className="flex h-8 items-center gap-1.5 text-sm">
          <input
            type="checkbox"
            checked={needsAttentionOnly}
            onChange={(e) => setNeedsAttentionOnly(e.target.checked)}
          />
          Needs attention only
        </label>
      </div>

      {isLoading && <p>Loading...</p>}
      {error && <p className="text-destructive">Failed to load series.</p>}
      {data && visibleSeries.length === 0 && (
        <p className="text-muted-foreground">No series tracked</p>
      )}
      {statusMessage && (
        <p className="text-sm text-muted-foreground">{statusMessage}</p>
      )}

      {data && visibleSeries.length > 0 && (
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-border border-b text-xs text-muted-foreground">
              <th className="w-8 py-2" />
              <th className="py-2 pr-4">Name</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2 pr-4">Tracked</th>
              <th className="py-2 pr-4">Chapter</th>
              <th className="py-2 pr-4">Last updated</th>
              <th className="w-8 py-2" />
            </tr>
          </thead>
          <tbody>
            {visibleSeries.map((row) => {
              const tier = stalenessTier(row.latest_chapter_date)
              const expanded = openId === row.entity_id
              return (
                <Fragment key={row.entity_id}>
                  <tr className="border-border border-b">
                    <td className={cn('py-2 pl-2', ACCENT_CLASS[tier])}>
                      <button
                        type="button"
                        aria-label={expanded ? 'Collapse' : 'Expand'}
                        onClick={() =>
                          setOpenId(expanded ? null : row.entity_id)
                        }
                        className="text-muted-foreground"
                      >
                        {expanded ? (
                          <ChevronDown className="size-4" />
                        ) : (
                          <ChevronRight className="size-4" />
                        )}
                      </button>
                    </td>
                    <td
                      className="max-w-64 truncate py-2 pr-4"
                      title={row.name}
                    >
                      <a
                        href={row.name_link}
                        target="_blank"
                        rel="noreferrer"
                        className="hover:underline"
                      >
                        {row.name}
                      </a>
                    </td>
                    <td className="py-2 pr-4">
                      <StatusBadge status={row.status} />
                    </td>
                    <td className="py-2 pr-4">
                      <TrackedBadge tracked={row.tracked} />
                    </td>
                    <td className="py-2 pr-4">{row.latest_chapter ?? '—'}</td>
                    <td
                      className="py-2 pr-4"
                      title={row.latest_chapter_date ?? undefined}
                    >
                      {formatRelative(row.latest_chapter_date)}
                    </td>
                    <td className="py-2 pr-2 text-right">
                      <button
                        type="button"
                        aria-label={`Delete ${row.name}`}
                        onClick={() => setDeleteTarget(row)}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="size-4" />
                      </button>
                    </td>
                  </tr>
                  {expanded && (
                    <tr className="border-border border-b bg-muted/30">
                      <td colSpan={7} className="p-4">
                        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-4">
                          <div>
                            <dt className="text-xs text-muted-foreground">
                              Entity ID
                            </dt>
                            <dd className="font-mono">{row.entity_id}</dd>
                          </div>
                          <div>
                            <dt className="text-xs text-muted-foreground">
                              Plugin
                            </dt>
                            <dd>
                              <a
                                href={row.plugin_link}
                                target="_blank"
                                rel="noreferrer"
                                className="hover:underline"
                              >
                                {row.plugin}
                              </a>
                            </dd>
                          </div>
                          <div>
                            <dt className="text-xs text-muted-foreground">
                              Metadata updated
                            </dt>
                            <dd>
                              {formatRelative(row.metadata_updated)} (
                              {row.metadata_updated ?? '—'})
                            </dd>
                          </div>
                          <div>
                            <dt className="text-xs text-muted-foreground">
                              Chapter updated
                            </dt>
                            <dd>
                              {formatRelative(row.latest_chapter_date)} (
                              {row.latest_chapter_date ?? '—'})
                            </dd>
                          </div>
                        </dl>
                      </td>
                    </tr>
                  )}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      )}

      <AlertDialog.Root
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null)
        }}
      >
        <AlertDialog.Portal>
          <AlertDialog.Overlay className="fixed inset-0 z-50 bg-black/60 data-[state=closed]:animate-out data-[state=open]:animate-in data-[state=closed]:fade-out data-[state=open]:fade-in" />
          <AlertDialog.Content className="fixed top-1/2 left-1/2 z-50 w-full max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-card p-6 shadow-xl duration-200 data-[state=closed]:animate-out data-[state=open]:animate-in data-[state=closed]:fade-out data-[state=open]:fade-in">
            <AlertDialog.Title className="text-lg font-medium">
              Delete {deleteTarget?.name}?
            </AlertDialog.Title>
            <AlertDialog.Description className="mt-2 text-sm text-muted-foreground">
              This removes the series and its tracked chapters from the
              database. This cannot be undone.
            </AlertDialog.Description>
            <div className="mt-6 flex justify-end gap-2">
              <AlertDialog.Cancel asChild>
                <Button variant="outline">Cancel</Button>
              </AlertDialog.Cancel>
              <Button
                variant="destructive"
                disabled={deleteSeries.isPending}
                onClick={() =>
                  deleteTarget && deleteSeries.mutate(deleteTarget)
                }
              >
                Delete
              </Button>
            </div>
          </AlertDialog.Content>
        </AlertDialog.Portal>
      </AlertDialog.Root>
    </div>
  )
}

export default SeriesPage
