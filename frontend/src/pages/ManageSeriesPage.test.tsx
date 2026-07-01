import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '@/test/msw-server'
import ManageSeriesPage from './ManageSeriesPage'

function renderWithClient() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <ManageSeriesPage />
    </QueryClientProvider>,
  )
}

const SERIES = [{ name: 'Test Manga', entity_id: 'series-1' }]
const CHAPTERS = [{ entity_id: 'chapter-1', chapter_number: '5' }]

function mockSeriesAndChapters() {
  server.use(
    http.get('*/api/scanner/series', () =>
      HttpResponse.json({ series: SERIES }),
    ),
    http.get('*/api/scanner/series/series-1/chapters', () =>
      HttpResponse.json({ chapters: CHAPTERS }),
    ),
  )
}

describe('ManageSeriesPage', () => {
  it('lists series and loads chapters when one is selected', async () => {
    mockSeriesAndChapters()
    const user = userEvent.setup()
    renderWithClient()

    await user.click(screen.getByRole('combobox', { name: 'Select a series' }))
    await user.click(await screen.findByRole('option', { name: 'Test Manga' }))

    await user.click(screen.getByRole('combobox', { name: 'Select a chapter' }))
    expect(
      await screen.findByRole('option', { name: 'Chapter 5' }),
    ).toBeInTheDocument()
  })

  it('deletes the selected series', async () => {
    mockSeriesAndChapters()
    server.use(
      http.delete('*/api/scanner/series/series-1', () =>
        HttpResponse.json({ message: 'Series deleted successfully' }),
      ),
    )
    const user = userEvent.setup()
    renderWithClient()

    await user.click(screen.getByRole('combobox', { name: 'Select a series' }))
    await user.click(await screen.findByRole('option', { name: 'Test Manga' }))

    await user.click(
      screen.getByRole('button', { name: 'Delete Selected Series' }),
    )

    expect(
      await screen.findByText('Removed Test Manga from the database'),
    ).toBeInTheDocument()
  })

  it('shows a busy message when the scanner is locked', async () => {
    mockSeriesAndChapters()
    server.use(
      http.delete('*/api/scanner/series/series-1', () =>
        HttpResponse.json(
          { detail: 'Scanner is currently busy. Please wait.' },
          { status: 409 },
        ),
      ),
    )
    const user = userEvent.setup()
    renderWithClient()

    await user.click(screen.getByRole('combobox', { name: 'Select a series' }))
    await user.click(await screen.findByRole('option', { name: 'Test Manga' }))

    await user.click(
      screen.getByRole('button', { name: 'Delete Selected Series' }),
    )

    expect(
      await screen.findByText('Scanner is busy. Please wait and try again.'),
    ).toBeInTheDocument()
  })

  it('cleans orphaned files', async () => {
    mockSeriesAndChapters()
    server.use(
      http.post('*/api/scanner/clean-orphaned', () =>
        HttpResponse.json({ message: 'Orphaned files cleaned successfully' }),
      ),
    )
    const user = userEvent.setup()
    renderWithClient()

    await user.click(
      screen.getByRole('button', { name: 'Clean Orphaned Files' }),
    )

    expect(
      await screen.findByText('Orphaned files removed successfully'),
    ).toBeInTheDocument()
  })
})
