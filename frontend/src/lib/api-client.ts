import createClient from 'openapi-fetch'
import type { paths } from './api-schema'

export const apiClient = createClient<paths>({
  baseUrl: window.location.origin,
  // Resolve `fetch` lazily rather than capturing it at module-load time, so test
  // tooling (MSW) that monkey-patches `globalThis.fetch` after this module has
  // already loaded still intercepts requests made through this client.
  fetch: (...args: Parameters<typeof fetch>) => globalThis.fetch(...args),
})
