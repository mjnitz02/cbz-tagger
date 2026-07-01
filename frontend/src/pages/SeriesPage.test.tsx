import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { server } from '@/test/msw-server'
import SeriesPage from './SeriesPage'

const NOW = new Date('2026-07-01T00:00:00.000Z')

function daysAgo(days: number): string {
  return new Date(NOW.getTime() - days * 86_400_000).toISOString()
}

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

const SERIES = [
  {
    entity_id: 'alpha-id',
    name: 'Alpha Manga',
    name_link: 'https://example.com/title/alpha-id',
    status: 'ongoing',
    tracked: true,
    latest_chapter: '10',
    latest_chapter_date: daysAgo(10),
    metadata_updated: daysAgo(10),
    plugin: 'mdx',
    plugin_link: 'https://example.com/title/alpha-id',
  },
  {
    entity_id: 'beta-id',
    name: 'Beta Manga',
    name_link: 'https://example.com/title/beta-id',
    status: 'hiatus',
    tracked: false,
    latest_chapter: '5',
    latest_chapter_date: daysAgo(100),
    metadata_updated: daysAgo(100),
    plugin: 'mdx',
    plugin_link: 'https://example.com/title/beta-id',
  },
  {
    entity_id: 'gamma-id',
    name: 'Gamma Manga',
    name_link: 'https://example.com/title/gamma-id',
    status: 'completed',
    tracked: true,
    latest_chapter: '50',
    latest_chapter_date: daysAgo(200),
    metadata_updated: daysAgo(200),
    plugin: 'kal',
    plugin_link: 'https://example.com/title/gamma-id',
  },
  {
    entity_id: 'delta-id',
    name: 'Delta Manga',
    name_link: 'https://example.com/title/delta-id',
    status: 'ongoing',
    tracked: false,
    latest_chapter: null,
    latest_chapter_date: null,
    metadata_updated: null,
    plugin: 'mdx',
    plugin_link: 'https://example.com/title/delta-id',
  },
  {
    entity_id: 'echo-id',
    name: 'Echo Manga',
    name_link: 'https://example.com/title/echo-id',
    status: 'ongoing',
    tracked: true,
    latest_chapter: '1',
    latest_chapter_date: daysAgo(1),
    metadata_updated: daysAgo(1),
    plugin: 'mdx',
    plugin_link: 'https://example.com/title/echo-id',
  },
]

function mockSeries(series: unknown[] = SERIES) {
  server.use(
    http.get('*/api/scanner/state', () => HttpResponse.json({ series })),
  )
}

async function openRowMenu(
  user: ReturnType<typeof userEvent.setup>,
  seriesName: string,
) {
  await user.click(
    screen.getByRole('button', { name: `Actions for ${seriesName}` }),
  )
}

async function openActionsMenu(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: 'Actions' }))
}

function nameOrder() {
  return screen
    .getAllByRole('link')
    .filter((el) => el.getAttribute('href')?.includes('/title/'))
    .map((el) => el.textContent)
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true })
  vi.setSystemTime(NOW)
})

afterEach(() => {
  vi.useRealTimers()
})

describe('SeriesPage', () => {
  it('shows a loading state then renders all rows', async () => {
    mockSeries()
    renderWithClient()

    expect(screen.getByText('Loading...')).toBeInTheDocument()
    expect(await screen.findByText('Alpha Manga')).toBeInTheDocument()
    expect(screen.getByText('Beta Manga')).toBeInTheDocument()
    expect(screen.getByText('Gamma Manga')).toBeInTheDocument()
    expect(screen.getByText('Delta Manga')).toBeInTheDocument()
    expect(screen.getByText('Echo Manga')).toBeInTheDocument()
  })

  it('renders an empty state when there are no series', async () => {
    mockSeries([])
    renderWithClient()

    expect(await screen.findByText('No series tracked')).toBeInTheDocument()
  })

  it('filters rows by name search', async () => {
    mockSeries()
    const user = userEvent.setup()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    await user.type(screen.getByPlaceholderText('Search by name'), 'beta')

    expect(screen.getByText('Beta Manga')).toBeInTheDocument()
    expect(screen.queryByText('Alpha Manga')).not.toBeInTheDocument()
  })

  it('narrows by status facet', async () => {
    mockSeries()
    const user = userEvent.setup()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    await user.click(screen.getByRole('button', { name: /status/i }))
    await user.click(
      await screen.findByRole('menuitemcheckbox', { name: 'Hiatus' }),
    )

    expect(screen.getByText('Beta Manga')).toBeInTheDocument()
    expect(screen.queryByText('Alpha Manga')).not.toBeInTheDocument()
    expect(screen.queryByText('Gamma Manga')).not.toBeInTheDocument()
  })

  it('narrows by tracked state', async () => {
    mockSeries()
    const user = userEvent.setup()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    await user.click(screen.getByLabelText('Tracked'))
    await user.click(await screen.findByRole('option', { name: 'Untracked' }))

    expect(screen.getByText('Beta Manga')).toBeInTheDocument()
    expect(screen.getByText('Delta Manga')).toBeInTheDocument()
    expect(screen.queryByText('Alpha Manga')).not.toBeInTheDocument()
  })

  it('narrows by plugin', async () => {
    mockSeries()
    const user = userEvent.setup()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    await user.click(screen.getByLabelText('Plugin'))
    await user.click(await screen.findByRole('option', { name: 'kal' }))

    expect(screen.getByText('Gamma Manga')).toBeInTheDocument()
    expect(screen.queryByText('Alpha Manga')).not.toBeInTheDocument()
  })

  it('needs-attention only shows stale/null-date ongoing or hiatus rows', async () => {
    mockSeries()
    const user = userEvent.setup()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    await user.click(screen.getByLabelText('Needs attention only'))

    expect(screen.getByText('Beta Manga')).toBeInTheDocument()
    expect(screen.getByText('Delta Manga')).toBeInTheDocument()
    expect(screen.queryByText('Alpha Manga')).not.toBeInTheDocument()
    expect(screen.queryByText('Echo Manga')).not.toBeInTheDocument()
    expect(screen.queryByText('Gamma Manga')).not.toBeInTheDocument()
  })

  it('sorts by name A-Z by default', async () => {
    mockSeries()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    expect(nameOrder()).toEqual([
      'Alpha Manga',
      'Beta Manga',
      'Delta Manga',
      'Echo Manga',
      'Gamma Manga',
    ])
  })

  it('sorts stalest first, floating null dates to the top', async () => {
    mockSeries()
    const user = userEvent.setup()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    await user.click(screen.getByLabelText('Sort'))
    await user.click(
      await screen.findByRole('option', { name: 'Stalest first' }),
    )

    expect(nameOrder()).toEqual([
      'Delta Manga',
      'Gamma Manga',
      'Beta Manga',
      'Alpha Manga',
      'Echo Manga',
    ])
  })

  it('sorts by recently updated, with null dates last', async () => {
    mockSeries()
    const user = userEvent.setup()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    await user.click(screen.getByLabelText('Sort'))
    await user.click(
      await screen.findByRole('option', { name: 'Recently updated' }),
    )

    expect(nameOrder()).toEqual([
      'Echo Manga',
      'Alpha Manga',
      'Beta Manga',
      'Gamma Manga',
      'Delta Manga',
    ])
  })

  it('expands a row to reveal entity id, plugin link, and metadata updated', async () => {
    mockSeries()
    const user = userEvent.setup()
    renderWithClient()

    const nameCell = await screen.findByText('Alpha Manga')
    const row = nameCell.closest('tr')
    if (!row) throw new Error('row not found')

    await user.click(within(row).getByRole('button', { name: 'Expand' }))

    expect(screen.getByText('alpha-id')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'mdx' })).toHaveAttribute(
      'href',
      'https://example.com/title/alpha-id',
    )
    expect(screen.getByText('Metadata updated')).toBeInTheDocument()
  })

  it('applies the stale accent class to the stale row', async () => {
    mockSeries()
    renderWithClient()

    const nameCell = await screen.findByText('Beta Manga')
    const row = nameCell.closest('tr')
    if (!row) throw new Error('row not found')
    const firstCell = row.querySelector('td')

    expect(firstCell).toHaveClass('border-red-500')
  })

  it('renders an error message when the request fails', async () => {
    server.use(http.get('*/api/scanner/state', () => HttpResponse.error()))
    renderWithClient()

    expect(
      await screen.findByText('Failed to load series.'),
    ).toBeInTheDocument()
  })

  it('deletes a series after confirming', async () => {
    mockSeries()
    server.use(
      http.delete('*/api/scanner/series/alpha-id', () =>
        HttpResponse.json({ message: 'Series deleted successfully' }),
      ),
    )
    const user = userEvent.setup()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    await openRowMenu(user, 'Alpha Manga')
    await user.click(await screen.findByRole('menuitem', { name: 'Delete' }))

    expect(await screen.findByText('Delete Alpha Manga?')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Delete' }))

    expect(
      await screen.findByText('Removed Alpha Manga from the database'),
    ).toBeInTheDocument()
  })

  it('cancels the delete confirmation without calling the API', async () => {
    mockSeries()
    const user = userEvent.setup()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    await openRowMenu(user, 'Alpha Manga')
    await user.click(await screen.findByRole('menuitem', { name: 'Delete' }))
    await user.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(screen.queryByText('Delete Alpha Manga?')).not.toBeInTheDocument()
    expect(screen.getByText('Alpha Manga')).toBeInTheDocument()
  })

  it('shows a busy message when deleting while the scanner is locked', async () => {
    mockSeries()
    server.use(
      http.delete('*/api/scanner/series/alpha-id', () =>
        HttpResponse.json(
          { detail: 'Scanner is currently busy. Please wait.' },
          { status: 409 },
        ),
      ),
    )
    const user = userEvent.setup()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    await openRowMenu(user, 'Alpha Manga')
    await user.click(await screen.findByRole('menuitem', { name: 'Delete' }))
    await user.click(screen.getByRole('button', { name: 'Delete' }))

    expect(
      await screen.findByText('Scanner is busy. Please wait and try again.'),
    ).toBeInTheDocument()
  })

  it('opens the chapter downloads dialog from the actions menu, toggles a chapter, and saves', async () => {
    mockSeries()
    server.use(
      http.get('*/api/scanner/series/alpha-id/chapters', () =>
        HttpResponse.json({
          chapters: [
            { entity_id: 'chapter-1', chapter_number: '1', downloaded: true },
            { entity_id: 'chapter-2', chapter_number: '2', downloaded: false },
          ],
        }),
      ),
    )
    let putBody: unknown
    server.use(
      http.put(
        '*/api/scanner/series/alpha-id/downloads',
        async ({ request }) => {
          putBody = await request.json()
          return HttpResponse.json({
            message: 'Downloaded chapters updated successfully',
          })
        },
      ),
    )
    const user = userEvent.setup()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    await openRowMenu(user, 'Alpha Manga')
    await user.click(
      await screen.findByRole('menuitem', { name: 'Manage downloads' }),
    )

    expect(
      await screen.findByText('Manage downloads — Alpha Manga'),
    ).toBeInTheDocument()
    expect(screen.getByText('1 of 2 downloaded')).toBeInTheDocument()

    await user.click(screen.getByRole('checkbox', { name: 'Chapter 2' }))
    expect(screen.getByText('2 of 2 downloaded')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Save' }))

    expect(
      await screen.findByText('Updated downloaded chapters for Alpha Manga'),
    ).toBeInTheDocument()
    expect(putBody).toEqual({
      downloaded_chapter_ids: expect.arrayContaining([
        'chapter-1',
        'chapter-2',
      ]),
    })
    expect(
      screen.queryByText('Manage downloads — Alpha Manga'),
    ).not.toBeInTheDocument()
  })

  it('opens the config dialog from the actions menu', async () => {
    mockSeries()
    server.use(
      http.get('*/api/enums/env', () =>
        HttpResponse.json({ VERSION: '5.0.0', CONFIG_PATH: '/config' }),
      ),
    )
    const user = userEvent.setup()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    await openActionsMenu(user)
    await user.click(await screen.findByRole('menuitem', { name: 'Config' }))

    expect(await screen.findByText('Server Configuration')).toBeInTheDocument()
    expect(screen.getByText('CONFIG_PATH')).toBeInTheDocument()
    expect(screen.getByText('/config')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Close' }))
    expect(screen.queryByText('Server Configuration')).not.toBeInTheDocument()
  })

  it('cleans orphaned files from the actions menu', async () => {
    mockSeries()
    server.use(
      http.post('*/api/scanner/clean-orphaned', () =>
        HttpResponse.json({ message: 'Orphaned files cleaned successfully' }),
      ),
    )
    const user = userEvent.setup()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    await openActionsMenu(user)
    await user.click(
      await screen.findByRole('menuitem', { name: 'Clean orphaned files' }),
    )

    expect(
      await screen.findByText('Orphaned files removed successfully'),
    ).toBeInTheDocument()
  })

  it('shows a busy message when cleaning orphaned files while the scanner is locked', async () => {
    mockSeries()
    server.use(
      http.post('*/api/scanner/clean-orphaned', () =>
        HttpResponse.json(
          { detail: 'Scanner is currently busy. Please wait.' },
          { status: 409 },
        ),
      ),
    )
    const user = userEvent.setup()
    renderWithClient()

    await screen.findByText('Alpha Manga')
    await openActionsMenu(user)
    await user.click(
      await screen.findByRole('menuitem', { name: 'Clean orphaned files' }),
    )

    expect(
      await screen.findByText('Scanner is busy. Please wait and try again.'),
    ).toBeInTheDocument()
  })
})
