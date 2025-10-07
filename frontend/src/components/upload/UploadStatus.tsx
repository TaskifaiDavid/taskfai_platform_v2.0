import { Badge } from '@/components/ui/badge'
import type { Upload } from '@/types'
import { CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react'

interface UploadStatusProps {
  status: Upload['status']
}

const statusConfig = {
  pending: {
    icon: Clock,
    variant: 'outline' as const,
    label: 'Pending',
  },
  processing: {
    icon: Loader2,
    variant: 'secondary' as const,
    label: 'Processing',
  },
  completed: {
    icon: CheckCircle2,
    variant: 'success' as const,
    label: 'Completed',
  },
  failed: {
    icon: XCircle,
    variant: 'destructive' as const,
    label: 'Failed',
  },
}

export function UploadStatus({ status }: UploadStatusProps) {
  const config = statusConfig[status] || statusConfig.pending
  const Icon = config.icon

  return (
    <Badge variant={config.variant} className="gap-1.5">
      <Icon className={`h-3 w-3 ${status === 'processing' ? 'animate-spin' : ''}`} />
      {config.label}
    </Badge>
  )
}
