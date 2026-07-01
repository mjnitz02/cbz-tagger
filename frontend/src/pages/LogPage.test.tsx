import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '@/test/msw-server'
import LogPage from './LogPage'

function renderWithClient() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <LogPage />
    </QueryClientProvider>,
  )
}

describe('LogPage', () => {
  it('renders log contents returned by the API', async () => {
    server.use(
      http.get('*/api/logs', () =>
        HttpResponse.json({ logs: 'hello from the log file' }),
      ),
    )

    renderWithClient()

    expect(
      await screen.findByText('hello from the log file'),
    ).toBeInTheDocument()
  })

  it('renders an error message when the request fails', async () => {
    server.use(http.get('*/api/logs', () => HttpResponse.error()))

    renderWithClient()

    expect(await screen.findByText('Failed to load logs.')).toBeInTheDocument()
  })

  it('clears the log file when Clear is clicked', async () => {
    const user = userEvent.setup()
    let cleared = false

    server.use(
      http.get('*/api/logs', () =>
        HttpResponse.json({ logs: cleared ? '' : 'hello from the log file' }),
      ),
      http.post('*/api/logs/clear', () => {
        cleared = true
        return HttpResponse.json({ message: 'Log file cleared successfully' })
      }),
    )

    renderWithClient()

    expect(
      await screen.findByText('hello from the log file'),
    ).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Clear' }))

    await waitFor(() => {
      expect(
        screen.queryByText('hello from the log file'),
      ).not.toBeInTheDocument()
    })
  })
})
