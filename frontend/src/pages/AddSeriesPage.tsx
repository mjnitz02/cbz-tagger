import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { apiClient } from '@/lib/api-client'

type TrackingMode = 'Yes' | 'No' | 'Disable Tracking'

const BUSY_MESSAGE = 'Scanner is busy. Please wait and try again.'

function AddSeriesPage() {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedResultId, setSelectedResultId] = useState<string>()
  const [selectedTitleName, setSelectedTitleName] = useState<string>()
  const [selectedBackend, setSelectedBackend] = useState<string>()
  const [backendId, setBackendId] = useState('')
  const [trackingMode, setTrackingMode] = useState<TrackingMode>('No')
  const [statusMessage, setStatusMessage] = useState<string>()

  const pluginsQuery = useQuery({
    queryKey: ['plugins'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/enums/plugins')
      if (error) throw error
      return data
    },
  })

  useEffect(() => {
    if (pluginsQuery.data && !selectedBackend) {
      setSelectedBackend(pluginsQuery.data.DEFAULT)
    }
  }, [pluginsQuery.data, selectedBackend])

  const search = useMutation({
    mutationFn: async () => {
      if (searchTerm.trim().length === 0) {
        throw new Error('Please enter a name to search for')
      }
      const { data, error } = await apiClient.GET(
        '/api/scanner/search-series',
        {
          params: { query: { title: searchTerm } },
        },
      )
      if (error) throw error
      return data
    },
    onSuccess: (data) => {
      const first = data.results[0]
      setSelectedResultId(first?.entity_id)
      setSelectedTitleName(first?.all_titles[0])
    },
  })

  const selectedResult = search.data?.results.find(
    (r) => r.entity_id === selectedResultId,
  )

  const addSeries = useMutation({
    mutationFn: async () => {
      const backend =
        selectedBackend && selectedBackend !== pluginsQuery.data?.DEFAULT
          ? { plugin_type: selectedBackend, plugin_id: backendId }
          : null

      const { response } = await apiClient.POST('/api/scanner/add-series', {
        body: {
          entity_name: selectedTitleName!,
          entity_id: selectedResult!.entity_id,
          backend,
          enable_tracking: trackingMode !== 'Disable Tracking',
          mark_all_tracked: trackingMode === 'Yes',
        },
      })
      return response
    },
    onSuccess: (response) => {
      if (response.status === 409) {
        setStatusMessage(BUSY_MESSAGE)
        return
      }
      setStatusMessage('New series added!')
      setSearchTerm('')
      setSelectedResultId(undefined)
      setSelectedTitleName(undefined)
      setSelectedBackend(pluginsQuery.data?.DEFAULT)
      setBackendId('')
      setTrackingMode('No')
      queryClient.invalidateQueries({ queryKey: ['series'] })
    },
  })

  const needsBackendId =
    !!selectedBackend && selectedBackend !== pluginsQuery.data?.DEFAULT
  const canAddSeries =
    !!selectedResult &&
    !!selectedTitleName &&
    (!needsBackendId || backendId.trim().length > 0)

  return (
    <div className="flex flex-col gap-4 p-4">
      <h1 className="text-2xl font-medium">Add Series</h1>

      <div className="flex max-w-md flex-col gap-1.5">
        <Label htmlFor="series-search">
          Please enter the name of a series to search for
        </Label>
        <Input
          id="series-search"
          placeholder="Series Name"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <Button
          variant="outline"
          className="self-start"
          disabled={search.isPending}
          onClick={() => search.mutate()}
        >
          Search for New Series
        </Button>
        {search.error && (
          <p className="text-sm text-destructive">
            {search.error instanceof Error
              ? search.error.message
              : 'Error searching for series.'}
          </p>
        )}
      </div>

      <div className="flex max-w-md flex-col gap-1.5">
        <Label htmlFor="result-select">Select a series (type to filter)</Label>
        <Select
          value={selectedResultId}
          onValueChange={(value) => {
            setSelectedResultId(value)
            const result = search.data?.results.find(
              (r) => r.entity_id === value,
            )
            setSelectedTitleName(result?.all_titles[0])
          }}
        >
          <SelectTrigger id="result-select" className="w-full">
            <SelectValue placeholder="Please search for a series" />
          </SelectTrigger>
          <SelectContent>
            {search.data?.results.map((result) => (
              <SelectItem key={result.entity_id} value={result.entity_id}>
                {result.display_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex max-w-md flex-col gap-1.5">
        <Label htmlFor="name-select">
          Select the name of the series (type to filter)
        </Label>
        <Select value={selectedTitleName} onValueChange={setSelectedTitleName}>
          <SelectTrigger id="name-select" className="w-full">
            <SelectValue placeholder="Please search for a series" />
          </SelectTrigger>
          <SelectContent>
            {selectedResult?.all_titles.map((title) => (
              <SelectItem key={title} value={title}>
                {title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex max-w-md flex-col gap-1.5">
        <Label htmlFor="backend-select">
          Select a series backend (Default: MDX)
        </Label>
        <Select value={selectedBackend} onValueChange={setSelectedBackend}>
          <SelectTrigger id="backend-select" className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {pluginsQuery.data?.all.map((plugin) => (
              <SelectItem key={plugin} value={plugin}>
                {plugin}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {needsBackendId && (
        <div className="flex max-w-md flex-col gap-1.5">
          <Label htmlFor="backend-id">
            Backend id for the series (Only for non-MDX backends)
          </Label>
          <Input
            id="backend-id"
            placeholder="Enter the backend id for the series"
            value={backendId}
            onChange={(e) => setBackendId(e.target.value)}
          />
        </div>
      )}

      <div className="flex flex-col gap-1.5">
        <Label>Mark all chapters as tracked?</Label>
        <RadioGroup
          className="flex flex-row gap-4"
          value={trackingMode}
          onValueChange={(value) => setTrackingMode(value as TrackingMode)}
        >
          {(['Yes', 'No', 'Disable Tracking'] as const).map((mode) => (
            <div key={mode} className="flex items-center gap-2">
              <RadioGroupItem value={mode} id={`tracking-${mode}`} />
              <Label htmlFor={`tracking-${mode}`}>{mode}</Label>
            </div>
          ))}
        </RadioGroup>
      </div>

      <div className="flex items-center gap-2">
        <Button
          disabled={!canAddSeries || addSeries.isPending}
          onClick={() => addSeries.mutate()}
        >
          Add New Series
        </Button>
        {addSeries.isPending && (
          <span className="text-muted-foreground text-sm">
            Adding new series...
          </span>
        )}
      </div>

      {statusMessage && (
        <p className="text-muted-foreground text-sm">{statusMessage}</p>
      )}
    </div>
  )
}

export default AddSeriesPage
