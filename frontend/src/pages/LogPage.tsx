import { useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api-client'

const REFRESH_INTERVAL_MS = 3000

function LogPage() {
  const queryClient = useQueryClient()
  const logContainerRef = useRef<HTMLPreElement>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['logs'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/logs', {
        params: { query: { max_lines: 1000 } },
      })
      if (error) throw error
      return data
    },
    refetchInterval: REFRESH_INTERVAL_MS,
  })

  const clearLogs = useMutation({
    mutationFn: async () => {
      const { error } = await apiClient.POST('/api/logs/clear')
      if (error) throw error
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['logs'] }),
  })

  useEffect(() => {
    const el = logContainerRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [data])

  return (
    <div className="p-4">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-medium">Log</h1>
        <Button
          variant="destructive"
          onClick={() => clearLogs.mutate()}
          disabled={clearLogs.isPending}
        >
          Clear
        </Button>
      </div>
      {isLoading && <p>Loading...</p>}
      {error && <p>Failed to load logs.</p>}
      {data && (
        <pre
          ref={logContainerRef}
          className="h-[70vh] w-full overflow-y-auto rounded-md bg-[#1e1e1e] p-2.5 font-mono text-xs whitespace-pre-wrap text-[#d4d4d4]"
        >
          {data.logs}
        </pre>
      )}
    </div>
  )
}

export default LogPage
