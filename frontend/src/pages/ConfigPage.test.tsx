import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '@/test/msw-server'
import ConfigPage from './ConfigPage'

function renderWithClient() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <ConfigPage />
    </QueryClientProvider>,
  )
}

describe('ConfigPage', () => {
  it('renders config values returned by the API', async () => {
    server.use(
      http.get('*/api/enums/env', () =>
        HttpResponse.json({
          VERSION: '4.3.1',
          PUID: 1000,
          PGID: 1000,
          DEBUG_MODE: false,
          UMASK: '022',
          CONFIG_PATH: '/config',
          SCAN_PATH: '/scan',
          STORAGE_PATH: '/storage',
          LOG_PATH: '/config/logs/cbz_tagger.log',
          TIMER_DELAY: 6000,
          PROXY_URL: null,
          DELAY_PER_REQUEST: 0.5,
          LOG_LEVEL: 20,
        }),
      ),
    )

    renderWithClient()

    expect(await screen.findByText('CONFIG_PATH')).toBeInTheDocument()
    expect(screen.getByText('/config')).toBeInTheDocument()
    expect(screen.getByText('6000')).toBeInTheDocument()
  })

  it('renders an error message when the request fails', async () => {
    server.use(http.get('*/api/enums/env', () => HttpResponse.error()))

    renderWithClient()

    expect(
      await screen.findByText('Failed to load configuration.'),
    ).toBeInTheDocument()
  })
})
