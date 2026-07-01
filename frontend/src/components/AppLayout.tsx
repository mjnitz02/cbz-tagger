import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Dialog } from 'radix-ui'
import { Library, Menu, X } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { cn } from '@/lib/utils'

const NAV_LINKS = [
  { to: '/series', label: 'Series' },
  { to: '/add_series', label: 'Add Series' },
  { to: '/config', label: 'Config' },
  { to: '/log', label: 'Log' },
]

function useVersion() {
  const { data } = useQuery({
    queryKey: ['env-config'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/enums/env')
      if (error) throw error
      return data
    },
    staleTime: Infinity,
  })
  return data?.VERSION
}

function VersionChip({
  version,
  className,
}: {
  version?: string
  className?: string
}) {
  if (!version) return null
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border border-border px-2 py-0.5 font-mono text-xs text-muted-foreground',
        className,
      )}
    >
      v{version}
    </span>
  )
}

function Brand({ className }: { className?: string }) {
  return (
    <span className={cn('flex items-center gap-2', className)}>
      <Library className="size-5 text-primary" />
      <span className="text-base font-semibold tracking-tight">CBZ Tagger</span>
    </span>
  )
}

export default function AppLayout() {
  const [open, setOpen] = useState(false)
  const version = useVersion()

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
        <div className="flex h-14 items-center gap-2 px-4">
          <NavLink to="/series" aria-label="CBZ Tagger home">
            <Brand />
          </NavLink>

          <nav className="ml-4 hidden items-center gap-1 md:flex">
            {NAV_LINKS.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  cn(
                    'relative rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'text-primary'
                      : 'text-muted-foreground hover:text-foreground',
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {label}
                    {isActive && (
                      <span className="absolute inset-x-3 -bottom-px h-0.5 rounded-full bg-primary" />
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <VersionChip version={version} className="hidden sm:inline-flex" />

            <Dialog.Root open={open} onOpenChange={setOpen}>
              <Dialog.Trigger asChild>
                <button
                  type="button"
                  aria-label="Open navigation"
                  className="inline-flex size-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground md:hidden"
                >
                  <Menu className="size-5" />
                </button>
              </Dialog.Trigger>
              <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 z-50 bg-black/60 data-[state=closed]:animate-out data-[state=open]:animate-in data-[state=closed]:fade-out data-[state=open]:fade-in" />
                <Dialog.Content className="fixed inset-y-0 left-0 z-50 flex w-72 max-w-[80%] flex-col border-r border-border bg-card p-4 shadow-xl duration-200 data-[state=closed]:animate-out data-[state=open]:animate-in data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left">
                  <div className="flex items-center justify-between">
                    <Dialog.Title asChild>
                      <Brand />
                    </Dialog.Title>
                    <Dialog.Close asChild>
                      <button
                        type="button"
                        aria-label="Close navigation"
                        className="inline-flex size-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                      >
                        <X className="size-5" />
                      </button>
                    </Dialog.Close>
                  </div>

                  <nav className="mt-6 flex flex-col gap-1">
                    {NAV_LINKS.map(({ to, label }) => (
                      <NavLink
                        key={to}
                        to={to}
                        onClick={() => setOpen(false)}
                        className={({ isActive }) =>
                          cn(
                            'rounded-md px-3 py-2 text-sm font-medium transition-colors',
                            isActive
                              ? 'bg-primary/15 text-primary'
                              : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                          )
                        }
                      >
                        {label}
                      </NavLink>
                    ))}
                  </nav>

                  <div className="mt-auto pt-4">
                    <VersionChip version={version} />
                  </div>
                </Dialog.Content>
              </Dialog.Portal>
            </Dialog.Root>
          </div>
        </div>
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  )
}
