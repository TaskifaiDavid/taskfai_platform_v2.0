import { formatDistanceToNow } from 'date-fns'
import {
  X,
  FileText,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Copy,
  BarChart3,
} from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useBibbiUploadDetails } from '@/api/bibbi'
import { Spinner } from '@/components/ui/spinner'

interface BibbiUploadDetailProps {
  uploadId: string
  onClose: () => void
}

export function BibbiUploadDetail({ uploadId, onClose }: BibbiUploadDetailProps) {
  const { data: upload, isLoading } = useBibbiUploadDetails(uploadId)

  if (isLoading || !upload) {
    return (
      <Card className="p-12">
        <div className="flex flex-col items-center gap-4">
          <Spinner />
          <p className="text-sm text-muted-foreground">Loading upload details...</p>
        </div>
      </Card>
    )
  }

  const totalRows = upload.total_rows || 0
  const processedRows = upload.processed_rows || 0
  const failedRows = upload.failed_rows || 0
  const duplicatedRows = upload.duplicated_rows || 0
  const successRate = totalRows > 0 ? ((processedRows / totalRows) * 100).toFixed(1) : 0

  return (
    <Card className="p-6 border-2">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4">
            <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
              <FileText className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-semibold">{upload.filename}</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Upload ID: {upload.upload_id.substring(0, 8)}...
              </p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Status and Vendor */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 border rounded-lg">
            <div className="text-sm text-muted-foreground mb-2">Status</div>
            <Badge
              variant={
                upload.upload_status === 'completed'
                  ? 'default'
                  : upload.upload_status === 'failed'
                  ? 'destructive'
                  : 'secondary'
              }
              className="capitalize"
            >
              {upload.upload_status}
            </Badge>
          </div>

          <div className="p-4 border rounded-lg">
            <div className="text-sm text-muted-foreground mb-2">Vendor Detected</div>
            <div className="font-medium capitalize">
              {upload.vendor_name || 'Not detected'}
            </div>
          </div>

          <div className="p-4 border rounded-lg">
            <div className="text-sm text-muted-foreground mb-2">Uploaded</div>
            <div className="font-medium">
              {formatDistanceToNow(new Date(upload.upload_timestamp), { addSuffix: true })}
            </div>
          </div>
        </div>

        {/* Processing Statistics */}
        {totalRows > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Processing Statistics
              </h3>
              <div className="text-2xl font-bold text-primary">{successRate}%</div>
            </div>

            {/* Progress Bar */}
            <Progress value={parseFloat(successRate)} className="h-2" />

            {/* Detailed Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 border rounded-lg bg-accent/5">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                    <TrendingUp className="h-5 w-5 text-blue-500" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold">{totalRows.toLocaleString()}</div>
                    <div className="text-xs text-muted-foreground">Total Rows</div>
                  </div>
                </div>
              </div>

              <div className="p-4 border rounded-lg bg-green-500/5">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {processedRows.toLocaleString()}
                    </div>
                    <div className="text-xs text-muted-foreground">Inserted</div>
                  </div>
                </div>
              </div>

              {duplicatedRows > 0 && (
                <div className="p-4 border rounded-lg bg-orange-500/5">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                      <Copy className="h-5 w-5 text-orange-500" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                        {duplicatedRows.toLocaleString()}
                      </div>
                      <div className="text-xs text-muted-foreground">Duplicates</div>
                    </div>
                  </div>
                </div>
              )}

              {failedRows > 0 && (
                <div className="p-4 border rounded-lg bg-red-500/5">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-red-500/10 flex items-center justify-center">
                      <XCircle className="h-5 w-5 text-red-500" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                        {failedRows.toLocaleString()}
                      </div>
                      <div className="text-xs text-muted-foreground">Failed</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Processing Timeline */}
        {upload.processing_started_at && (
          <div className="p-4 border rounded-lg bg-accent/5">
            <h3 className="text-sm font-semibold mb-3">Processing Timeline</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Started:</span>
                <span className="font-medium">
                  {new Date(upload.processing_started_at).toLocaleString()}
                </span>
              </div>
              {upload.processing_completed_at && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Completed:</span>
                  <span className="font-medium">
                    {new Date(upload.processing_completed_at).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Information */}
        {upload.processing_errors && (
          <div className="p-4 border border-red-500/50 rounded-lg bg-red-500/5">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1 space-y-2">
                <h3 className="font-semibold text-red-700 dark:text-red-400">
                  Processing Errors
                </h3>
                {upload.processing_errors.error_message && (
                  <p className="text-sm text-red-600 dark:text-red-300">
                    {upload.processing_errors.error_message}
                  </p>
                )}
                {upload.processing_errors.validation_errors && (
                  <details className="text-sm">
                    <summary className="cursor-pointer text-red-600 dark:text-red-300 hover:underline">
                      View validation errors
                    </summary>
                    <pre className="mt-2 p-3 bg-background rounded border text-xs overflow-auto max-h-60">
                      {JSON.stringify(upload.processing_errors.validation_errors, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          </div>
        )}

        {/* File Information */}
        <div className="p-4 border rounded-lg bg-accent/5">
          <h3 className="text-sm font-semibold mb-3">File Information</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">File Size:</span>
              <span className="ml-2 font-medium">
                {(upload.file_size / 1024 / 1024).toFixed(2)} MB
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">File Hash:</span>
              <span className="ml-2 font-mono text-xs">
                {upload.file_hash.substring(0, 16)}...
              </span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}
