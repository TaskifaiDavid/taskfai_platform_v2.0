import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import {
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Eye,
  RotateCcw,
  FileText,
} from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useBibbiUploadsList, useBibbiRetryUpload } from '@/api/bibbi'
import { Spinner } from '@/components/ui/spinner'

interface BibbiUploadHistoryProps {
  onViewDetails: (uploadId: string) => void
  selectedUploadId: string | null
}

const STATUS_ICONS = {
  pending: Clock,
  processing: Loader2,
  validated: CheckCircle2,
  completed: CheckCircle2,
  failed: XCircle,
  partial: AlertCircle,
}

const STATUS_COLORS = {
  pending: 'text-yellow-500',
  processing: 'text-blue-500',
  validated: 'text-green-500',
  completed: 'text-green-500',
  failed: 'text-red-500',
  partial: 'text-orange-500',
}

const STATUS_BG_COLORS = {
  pending: 'bg-yellow-500/10 border-yellow-500/50',
  processing: 'bg-blue-500/10 border-blue-500/50',
  validated: 'bg-green-500/10 border-green-500/50',
  completed: 'bg-green-500/10 border-green-500/50',
  failed: 'bg-red-500/10 border-red-500/50',
  partial: 'bg-orange-500/10 border-orange-500/50',
}

export function BibbiUploadHistory({ onViewDetails, selectedUploadId }: BibbiUploadHistoryProps) {
  const [statusFilter, setStatusFilter] = useState<string>('')
  const { data, isLoading } = useBibbiUploadsList(statusFilter)
  const retryMutation = useBibbiRetryUpload()

  const handleRetry = async (uploadId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    try {
      await retryMutation.mutateAsync(uploadId)
    } catch (error) {
      console.error('Retry failed:', error)
    }
  }

  if (isLoading) {
    return (
      <Card className="p-12">
        <div className="flex flex-col items-center gap-4">
          <Spinner />
          <p className="text-sm text-muted-foreground">Loading upload history...</p>
        </div>
      </Card>
    )
  }

  const uploads = data?.uploads || []

  return (
    <Card className="p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Upload History</h2>
            <p className="text-sm text-muted-foreground mt-1">
              {uploads.length} upload{uploads.length !== 1 ? 's' : ''} total
            </p>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border rounded-lg bg-background text-sm"
            >
              <option value="">All statuses</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="partial">Partial</option>
            </select>
          </div>
        </div>

        {/* Table */}
        {uploads.length === 0 ? (
          <div className="py-12 text-center">
            <FileText className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground">No uploads yet</p>
            <p className="text-sm text-muted-foreground/70 mt-1">
              Upload an Excel file to get started
            </p>
          </div>
        ) : (
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Filename</TableHead>
                  <TableHead>Vendor</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Rows</TableHead>
                  <TableHead>Uploaded</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {uploads.map((upload) => {
                  const StatusIcon = STATUS_ICONS[upload.upload_status] || Clock
                  const isSelected = upload.upload_id === selectedUploadId

                  return (
                    <TableRow
                      key={upload.upload_id}
                      className={`cursor-pointer hover:bg-accent/50 ${
                        isSelected ? 'bg-accent/30' : ''
                      }`}
                      onClick={() => onViewDetails(upload.upload_id)}
                    >
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          <span className="truncate max-w-[200px]">{upload.filename}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {upload.vendor_name ? (
                          <Badge variant="secondary" className="capitalize">
                            {upload.vendor_name}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground text-sm">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className={`flex items-center gap-2 ${STATUS_COLORS[upload.upload_status]}`}>
                          <StatusIcon
                            className={`h-4 w-4 ${
                              upload.upload_status === 'processing' ? 'animate-spin' : ''
                            }`}
                          />
                          <span className="capitalize text-sm">{upload.upload_status}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        {upload.total_rows ? (
                          <div className="space-y-1">
                            <div className="text-sm font-medium">{upload.total_rows.toLocaleString()}</div>
                            {(upload.processed_rows || upload.failed_rows || upload.duplicated_rows) && (
                              <div className="text-xs text-muted-foreground">
                                {upload.processed_rows && (
                                  <span className="text-green-600 dark:text-green-400">
                                    {upload.processed_rows} ✓
                                  </span>
                                )}
                                {upload.duplicated_rows && upload.duplicated_rows > 0 && (
                                  <span className="text-orange-600 dark:text-orange-400 ml-2">
                                    {upload.duplicated_rows} ⊗
                                  </span>
                                )}
                                {upload.failed_rows && upload.failed_rows > 0 && (
                                  <span className="text-red-600 dark:text-red-400 ml-2">
                                    {upload.failed_rows} ✗
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-muted-foreground text-sm">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-muted-foreground">
                          {formatDistanceToNow(new Date(upload.upload_timestamp), { addSuffix: true })}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              onViewDetails(upload.upload_id)
                            }}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {upload.upload_status === 'failed' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => handleRetry(upload.upload_id, e)}
                              disabled={retryMutation.isPending}
                            >
                              <RotateCcw
                                className={`h-4 w-4 ${
                                  retryMutation.isPending ? 'animate-spin' : ''
                                }`}
                              />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </Card>
  )
}
