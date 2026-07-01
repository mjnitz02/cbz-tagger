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

async function selectSeriesAndChapter(
  user: ReturnType<typeof userEvent.setup>,
) {
  await user.click(screen.getByRole('combobox', { name: 'Select a series' }))
  await user.click(await screen.findByRole('option', { name: 'Test Manga' }))

  await user.click(screen.getByRole('combobox', { name: 'Select a chapter' }))
  await user.click(await screen.findByRole('option', { name: 'Chapter 5' }))
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

  it('resets a tracked chapter', async () => {
    mockSeriesAndChapters()
    server.use(
      http.delete('*/api/scanner/chapter/series-1/chapter-1', () =>
        HttpResponse.json({ message: 'Chapter tracking removed' }),
      ),
    )
    const user = userEvent.setup()
    renderWithClient()

    await selectSeriesAndChapter(user)
    await user.click(
      screen.getByRole('button', { name: 'Reset Tracked Chapter' }),
    )

    expect(
      await screen.findByText('Removed tracked status for 5 from Test Manga'),
    ).toBeInTheDocument()
  })

  it('shows a busy message when the scanner is locked', async () => {
    mockSeriesAndChapters()
    server.use(
      http.delete('*/api/scanner/chapter/series-1/chapter-1', () =>
        HttpResponse.json(
          { detail: 'Scanner is currently busy. Please wait.' },
          { status: 409 },
        ),
      ),
    )
    const user = userEvent.setup()
    renderWithClient()

    await selectSeriesAndChapter(user)
    await user.click(
      screen.getByRole('button', { name: 'Reset Tracked Chapter' }),
    )

    expect(
      await screen.findByText('Scanner is busy. Please wait and try again.'),
    ).toBeInTheDocument()
  })
})
