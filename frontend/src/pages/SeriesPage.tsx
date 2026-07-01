import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

function SeriesPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['series'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/scanner/series')
      if (error) throw error
      return data
    },
  })

  return (
    <div>
      <h1>Series</h1>
      {isLoading && <p>Loading...</p>}
      {error && <p>Failed to load series.</p>}
      {data && (
        <ul>
          {data.series.map((series) => (
            <li key={series.entity_id}>{series.name}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default SeriesPage
