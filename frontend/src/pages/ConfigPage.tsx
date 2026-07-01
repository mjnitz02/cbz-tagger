import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api-client'

const BUSY_MESSAGE = 'Scanner is busy. Please wait and try again.'

function ConfigPage() {
  const queryClient = useQueryClient()
  const [statusMessage, setStatusMessage] = useState<string>()

  const { data, isLoading, error } = useQuery({
    queryKey: ['env-config'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/enums/env')
      if (error) throw error
      return data
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
      queryClient.invalidateQueries({ queryKey: ['series-state'] })
    },
  })

  return (
    <div className="p-4">
      <h1 className="mb-4 text-2xl font-medium">Server Configuration</h1>
      {isLoading && <p>Loading...</p>}
      {error && <p>Failed to load configuration.</p>}
      {data && (
        <table className="w-full max-w-2xl border-collapse text-left text-sm">
          <tbody>
            {Object.entries(data).map(([property, value]) => (
              <tr key={property} className="border-border border-b">
                <td className="py-2 pr-4 font-medium">{property}</td>
                <td className="py-2 text-muted-foreground">{String(value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="mt-6 flex max-w-2xl flex-col items-start gap-2 border-t border-border pt-4">
        <h2 className="text-sm font-medium">Maintenance</h2>
        <Button
          variant="outline"
          disabled={cleanOrphanedFiles.isPending}
          onClick={() => cleanOrphanedFiles.mutate()}
        >
          Clean Orphaned Files
        </Button>
        {statusMessage && (
          <p className="text-sm text-muted-foreground">{statusMessage}</p>
        )}
      </div>
    </div>
  )
}

export default ConfigPage
