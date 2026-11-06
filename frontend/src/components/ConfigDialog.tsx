import { useQuery } from '@tanstack/react-query'
import { Modal } from '@/components/ui/modal'
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
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title="Server Configuration"
      description="Read-only view of the values the server was configured with."
      className="max-w-lg"
    >
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
    </Modal>
  )
}

export default ConfigDialog
