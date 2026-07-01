import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

function ConfigPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['env-config'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/enums/env')
      if (error) throw error
      return data
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
    </div>
  )
}

export default ConfigPage
