import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Dialog } from 'radix-ui'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { apiClient } from '@/lib/api-client'

const BUSY_MESSAGE = 'Scanner is busy. Please wait and try again.'

interface ChapterDownloadsDialogProps {
  series: { entity_id: string; name: string } | null
  onOpenChange: (open: boolean) => void
  onStatusMessage: (message: string) => void
}

function setsAreEqual(a: Set<string>, b: Set<string>): boolean {
  if (a.size !== b.size) return false
  for (const value of a) {
    if (!b.has(value)) return false
  }
  return true
}

function ChapterDownloadsDialog({
  series,
  onOpenChange,
  onStatusMessage,
}: ChapterDownloadsDialogProps) {
  const entityId = series?.entity_id
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [working, setWorking] = useState<Set<string>>(new Set())
  const [seed, setSeed] = useState<Set<string>>(new Set())

  const chaptersQuery = useQuery({
    queryKey: ['chapters', entityId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        '/api/scanner/series/{entity_id}/chapters',
        { params: { path: { entity_id: entityId! } } },
      )
      if (error) throw error
      return data
    },
    enabled: !!entityId,
  })

  useEffect(() => {
    if (!chaptersQuery.data) return
    const downloaded = new Set(
      chaptersQuery.data.chapters
        .filter((c) => c.downloaded)
        .map((c) => c.entity_id),
    )
    setWorking(downloaded)
    setSeed(downloaded)
  }, [chaptersQuery.data])

  useEffect(() => {
    if (!series) setSearch('')
  }, [series])

  const chapters = useMemo(
    () => chaptersQuery.data?.chapters ?? [],
    [chaptersQuery.data],
  )

  const filteredChapters = useMemo(() => {
    const term = search.toLowerCase().trim()
    if (term === '') return chapters
    return chapters.filter((c) => c.chapter_number.toLowerCase().includes(term))
  }, [chapters, search])

  const dirty = !setsAreEqual(working, seed)

  const setDownloads = useMutation({
    mutationFn: async () => {
      const { response } = await apiClient.PUT(
        '/api/scanner/series/{entity_id}/downloads',
        {
          params: { path: { entity_id: entityId! } },
          body: { downloaded_chapter_ids: [...working] },
        },
      )
      return response
    },
    onSuccess: (response) => {
      if (response.status === 409) {
        onStatusMessage(BUSY_MESSAGE)
        return
      }
      onStatusMessage(`Updated downloaded chapters for ${series?.name}`)
      queryClient.invalidateQueries({ queryKey: ['chapters', entityId] })
      queryClient.invalidateQueries({ queryKey: ['series-state'] })
      onOpenChange(false)
    },
  })

  function toggleChapter(chapterId: string) {
    setWorking((prev) => {
      const next = new Set(prev)
      if (next.has(chapterId)) {
        next.delete(chapterId)
      } else {
        next.add(chapterId)
      }
      return next
    })
  }

  function selectAllFiltered() {
    setWorking((prev) => {
      const next = new Set(prev)
      for (const c of filteredChapters) next.add(c.entity_id)
      return next
    })
  }

  function clearAllFiltered() {
    setWorking((prev) => {
      const next = new Set(prev)
      for (const c of filteredChapters) next.delete(c.entity_id)
      return next
    })
  }

  return (
    <Dialog.Root
      open={series !== null}
      onOpenChange={(open) => {
        if (!open) onOpenChange(false)
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/60 data-[state=closed]:animate-out data-[state=open]:animate-in data-[state=closed]:fade-out data-[state=open]:fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 z-50 flex max-h-[85vh] w-full max-w-md -translate-x-1/2 -translate-y-1/2 flex-col rounded-lg border border-border bg-card p-6 shadow-xl duration-200 data-[state=closed]:animate-out data-[state=open]:animate-in data-[state=closed]:fade-out data-[state=open]:fade-in">
          <div className="flex items-start justify-between gap-4">
            <Dialog.Title className="text-lg font-medium">
              Manage downloads — {series?.name}
            </Dialog.Title>
            <Dialog.Close asChild>
              <button
                type="button"
                aria-label="Close"
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="size-5" />
              </button>
            </Dialog.Close>
          </div>

          <Dialog.Description className="mt-2 text-sm text-muted-foreground">
            Checked = downloaded (won&apos;t re-download). Unchecked = will be
            re-downloaded on next refresh.
          </Dialog.Description>

          <div className="mt-4 flex items-center gap-2">
            <Input
              placeholder="Search chapters"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={selectAllFiltered}
            >
              Select all
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={clearAllFiltered}
            >
              Clear all
            </Button>
          </div>

          <p className="mt-2 text-xs text-muted-foreground">
            {working.size} of {chapters.length} downloaded
          </p>

          {chaptersQuery.isLoading && (
            <p className="mt-4 text-sm text-muted-foreground">Loading...</p>
          )}
          {chaptersQuery.error && (
            <p className="mt-4 text-sm text-destructive">
              Failed to load chapters.
            </p>
          )}

          <div className="mt-2 max-h-72 flex-1 overflow-y-auto rounded-md border border-border">
            {filteredChapters.map((chapter) => (
              <label
                key={chapter.entity_id}
                className="flex cursor-pointer items-center gap-2 border-b border-border px-3 py-2 text-sm last:border-b-0 hover:bg-muted/50"
              >
                <input
                  type="checkbox"
                  checked={working.has(chapter.entity_id)}
                  onChange={() => toggleChapter(chapter.entity_id)}
                />
                Chapter {chapter.chapter_number}
              </label>
            ))}
            {!chaptersQuery.isLoading && filteredChapters.length === 0 && (
              <p className="px-3 py-2 text-sm text-muted-foreground">
                No chapters found.
              </p>
            )}
          </div>

          {setDownloads.isError && (
            <p className="mt-2 text-sm text-destructive">
              Failed to update downloaded chapters.
            </p>
          )}

          <div className="mt-6 flex justify-end gap-2">
            <Dialog.Close asChild>
              <Button variant="outline">Cancel</Button>
            </Dialog.Close>
            <Button
              disabled={!dirty || setDownloads.isPending}
              onClick={() => setDownloads.mutate()}
            >
              Save
            </Button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

export default ChapterDownloadsDialog
