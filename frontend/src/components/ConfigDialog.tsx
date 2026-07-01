import { useQuery } from '@tanstack/react-query'
import { Dialog } from 'radix-ui'
import { X } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface ConfigDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

function ConfigDialog({ open, onOpenChange }: ConfigDialogProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['env-config'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/enums/env')
      if (error) throw error
      return data
    },
    enabled: open,
  })

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/60 data-[state=closed]:animate-out data-[state=open]:animate-in data-[state=closed]:fade-out data-[state=open]:fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 z-50 flex max-h-[85vh] w-full max-w-lg -translate-x-1/2 -translate-y-1/2 flex-col rounded-lg border border-border bg-card p-6 shadow-xl duration-200 data-[state=closed]:animate-out data-[state=open]:animate-in data-[state=closed]:fade-out data-[state=open]:fade-in">
          <div className="flex items-start justify-between gap-4">
            <Dialog.Title className="text-lg font-medium">
              Server Configuration
            </Dialog.Title>
            <Dialog.Close asChild>
              <button
                type="button"
                aria-label="Close"
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="size-5" />
              </button>
            </Dialog.Close>
          </div>

          <Dialog.Description className="mt-2 text-sm text-muted-foreground">
            Read-only view of the values the server was configured with.
          </Dialog.Description>

          {isLoading && <p className="mt-4 text-sm">Loading...</p>}
          {error && (
            <p className="mt-4 text-sm text-destructive">
              Failed to load configuration.
            </p>
          )}
          {data && (
            <div className="mt-4 overflow-y-auto">
              <table className="w-full border-collapse text-left text-sm">
                <tbody>
                  {Object.entries(data).map(([property, value]) => (
                    <tr key={property} className="border-border border-b">
                      <td className="py-2 pr-4 font-medium">{property}</td>
                      <td className="py-2 text-muted-foreground">
                        {String(value)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

export default ConfigDialog
