import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '@/test/msw-server'
import AddSeriesPage from './AddSeriesPage'

function renderWithClient() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <AddSeriesPage />
    </QueryClientProvider>,
  )
}

const SEARCH_RESULTS = [
  {
    entity_id: 'manga-1',
    title: 'Test Manga',
    alt_title: 'Alt Manga',
    all_titles: ['Test Manga', 'Alt Manga'],
    created_at_year: 2020,
    age_rating: 'safe',
    display_name: 'Test Manga (Alt Manga) - 2020 - safe',
  },
]

function mockPlugins() {
  server.use(
    http.get('*/api/enums/plugins', () =>
      HttpResponse.json({ DEFAULT: 'mdx', all: ['mdx', 'kal'] }),
    ),
  )
}

describe('AddSeriesPage', () => {
  it('searches for a series and populates the cascading selects', async () => {
    mockPlugins()
    server.use(
      http.get('*/api/scanner/search-series', () =>
        HttpResponse.json({ results: SEARCH_RESULTS }),
      ),
    )
    const user = userEvent.setup()
    renderWithClient()

    await user.type(
      screen.getByLabelText('Please enter the name of a series to search for'),
      'Test',
    )
    await user.click(
      screen.getByRole('button', { name: 'Search for New Series' }),
    )

    expect(
      await screen.findByRole('combobox', {
        name: 'Select a series (type to filter)',
      }),
    ).toHaveTextContent('Test Manga (Alt Manga) - 2020 - safe')
    expect(
      screen.getByRole('combobox', {
        name: 'Select the name of the series (type to filter)',
      }),
    ).toHaveTextContent('Test Manga')
  })

  it('shows an error when searching with an empty term', async () => {
    mockPlugins()
    const user = userEvent.setup()
    renderWithClient()

    await user.click(
      screen.getByRole('button', { name: 'Search for New Series' }),
    )

    expect(
      await screen.findByText('Please enter a name to search for'),
    ).toBeInTheDocument()
  })

  it('adds the selected series', async () => {
    mockPlugins()
    server.use(
      http.get('*/api/scanner/search-series', () =>
        HttpResponse.json({ results: SEARCH_RESULTS }),
      ),
      http.post('*/api/scanner/add-series', async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>
        expect(body).toMatchObject({
          entity_name: 'Test Manga',
          entity_id: 'manga-1',
          backend: null,
          enable_tracking: true,
          mark_all_tracked: false,
        })
        return HttpResponse.json({
          message: "Series 'Test Manga' added successfully",
        })
      }),
    )
    const user = userEvent.setup()
    renderWithClient()

    await user.type(
      screen.getByLabelText('Please enter the name of a series to search for'),
      'Test',
    )
    await user.click(
      screen.getByRole('button', { name: 'Search for New Series' }),
    )
    await screen.findByRole('combobox', {
      name: 'Select a series (type to filter)',
    })

    await user.click(screen.getByRole('button', { name: 'Add New Series' }))

    expect(await screen.findByText('New series added!')).toBeInTheDocument()
  })

  it('requires a backend id for non-default backends', async () => {
    mockPlugins()
    server.use(
      http.get('*/api/scanner/search-series', () =>
        HttpResponse.json({ results: SEARCH_RESULTS }),
      ),
    )
    const user = userEvent.setup()
    renderWithClient()

    await user.type(
      screen.getByLabelText('Please enter the name of a series to search for'),
      'Test',
    )
    await user.click(
      screen.getByRole('button', { name: 'Search for New Series' }),
    )
    await screen.findByRole('combobox', {
      name: 'Select a series (type to filter)',
    })

    await user.click(
      screen.getByRole('combobox', {
        name: 'Select a series backend (Default: MDX)',
      }),
    )
    await user.click(await screen.findByRole('option', { name: 'kal' }))

    expect(
      screen.getByRole('button', { name: 'Add New Series' }),
    ).toBeDisabled()

    await user.type(
      screen.getByLabelText(
        'Backend id for the series (Only for non-MDX backends)',
      ),
      'kal-id',
    )

    expect(screen.getByRole('button', { name: 'Add New Series' })).toBeEnabled()
  })
})
