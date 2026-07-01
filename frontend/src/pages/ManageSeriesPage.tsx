import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { apiClient } from '@/lib/api-client'

const BUSY_MESSAGE = 'Scanner is busy. Please wait and try again.'

function ManageSeriesPage() {
  const queryClient = useQueryClient()
  const [selectedSeriesId, setSelectedSeriesId] = useState<string>()
  const [selectedChapterId, setSelectedChapterId] = useState<string>()
  const [statusMessage, setStatusMessage] = useState<string>()

  const seriesQuery = useQuery({
    queryKey: ['series'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/scanner/series')
      if (error) throw error
      return data
    },
  })

  const chaptersQuery = useQuery({
    queryKey: ['chapters', selectedSeriesId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        '/api/scanner/series/{entity_id}/chapters',
        {
          params: { path: { entity_id: selectedSeriesId! } },
        },
      )
      if (error) throw error
      return data
    },
    enabled: !!selectedSeriesId,
  })

  const selectedSeries = seriesQuery.data?.series.find(
    (s) => s.entity_id === selectedSeriesId,
  )
  const selectedChapter = chaptersQuery.data?.chapters.find(
    (c) => c.entity_id === selectedChapterId,
  )

  const deleteSeries = useMutation({
    mutationFn: async () => {
      const { response } = await apiClient.DELETE(
        '/api/scanner/series/{entity_id}',
        {
          params: {
            path: { entity_id: selectedSeriesId! },
            query: { entity_name: selectedSeries!.name },
          },
        },
      )
      return response
    },
    onSuccess: (response) => {
      if (response.status === 409) {
        setStatusMessage(BUSY_MESSAGE)
        return
      }
      setStatusMessage(`Removed ${selectedSeries?.name} from the database`)
      setSelectedSeriesId(undefined)
      setSelectedChapterId(undefined)
      queryClient.invalidateQueries({ queryKey: ['series'] })
    },
  })

  const deleteChapterTracking = useMutation({
    mutationFn: async () => {
      const { response } = await apiClient.DELETE(
        '/api/scanner/chapter/{entity_id}/{chapter_id}',
        {
          params: {
            path: {
              entity_id: selectedSeriesId!,
              chapter_id: selectedChapterId!,
            },
          },
        },
      )
      return response
    },
    onSuccess: (response) => {
      if (response.status === 409) {
        setStatusMessage(BUSY_MESSAGE)
        return
      }
      setStatusMessage(
        `Removed tracked status for ${selectedChapter?.chapter_number} from ${selectedSeries?.name}`,
      )
      setSelectedChapterId(undefined)
      queryClient.invalidateQueries({
        queryKey: ['chapters', selectedSeriesId],
      })
    },
  })

  const cleanOrphanedFiles = useMutation({
    mutationFn: async () => {
      const { response } = await apiClient.POST('/api/scanner/clean-orphaned')
      return response
    },
    onSuccess: (response) => {
      if (response.status === 409) {
        setStatusMessage(BUSY_MESSAGE)
        return
      }
      setStatusMessage('Orphaned files removed successfully')
      queryClient.invalidateQueries({ queryKey: ['series'] })
    },
  })

  return (
    <div className="flex flex-col gap-4 p-4">
      <h1 className="text-2xl font-medium">Manage Series</h1>

      <div className="flex max-w-md flex-col gap-1.5">
        <Label htmlFor="series-select">Select a series</Label>
        <Select
          value={selectedSeriesId}
          onValueChange={(value) => {
            setSelectedSeriesId(value)
            setSelectedChapterId(undefined)
          }}
        >
          <SelectTrigger id="series-select" className="w-full">
            <SelectValue placeholder="Select a series" />
          </SelectTrigger>
          <SelectContent>
            {seriesQuery.data?.series.map((series) => (
              <SelectItem key={series.entity_id} value={series.entity_id}>
                {series.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex max-w-md flex-col gap-1.5">
        <Label htmlFor="chapter-select">Select a chapter</Label>
        <Select value={selectedChapterId} onValueChange={setSelectedChapterId}>
          <SelectTrigger id="chapter-select" className="w-full">
            <SelectValue placeholder="Select a series first" />
          </SelectTrigger>
          <SelectContent>
            {chaptersQuery.data?.chapters.map((chapter) => (
              <SelectItem key={chapter.entity_id} value={chapter.entity_id}>
                Chapter {chapter.chapter_number}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button variant="outline" onClick={() => seriesQuery.refetch()}>
          Refresh Series List
        </Button>
        <Button
          variant="destructive"
          disabled={!selectedSeriesId || deleteSeries.isPending}
          onClick={() => deleteSeries.mutate()}
        >
          Delete Selected Series
        </Button>
        <Button
          variant="outline"
          disabled={!selectedChapterId || deleteChapterTracking.isPending}
          onClick={() => deleteChapterTracking.mutate()}
        >
          Reset Tracked Chapter
        </Button>
        <Button
          variant="outline"
          disabled={cleanOrphanedFiles.isPending}
          onClick={() => cleanOrphanedFiles.mutate()}
        >
          Clean Orphaned Files
        </Button>
      </div>

      {statusMessage && (
        <p className="text-muted-foreground text-sm">{statusMessage}</p>
      )}
      {seriesQuery.error && (
        <p className="text-sm text-destructive">Failed to load series.</p>
      )}
    </div>
  )
}

export default ManageSeriesPage
