import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '@/test/msw-server'
import SeriesPage from './SeriesPage'

function renderWithClient() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <SeriesPage />
    </QueryClientProvider>,
  )
}

describe('SeriesPage', () => {
  it('renders series returned by the API', async () => {
    server.use(
      http.get('*/api/scanner/series', () =>
        HttpResponse.json({
          series: [{ name: 'Test Manga', entity_id: 'abc-123' }],
        }),
      ),
    )

    renderWithClient()

    expect(await screen.findByText('Test Manga')).toBeInTheDocument()
  })

  it('renders an error message when the request fails', async () => {
    server.use(http.get('*/api/scanner/series', () => HttpResponse.error()))

    renderWithClient()

    expect(
      await screen.findByText('Failed to load series.'),
    ).toBeInTheDocument()
  })
})
