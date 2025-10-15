import { useUploadsList } from '@/api/uploads'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { UploadStatus } from './UploadStatus'
import { Button } from '@/components/ui/button'
import { Eye, Loader2 } from 'lucide-react'

interface UploadHistoryProps {
  onViewDetails?: (batchId: string) => void
}

export function UploadHistory({ onViewDetails }: UploadHistoryProps) {
  const { data: uploads, isLoading } = useUploadsList()

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (!uploads || uploads.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Upload History</CardTitle>
          <CardDescription>No uploads yet</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload History</CardTitle>
        <CardDescription>Recent file uploads and their processing status</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Filename</TableHead>
              <TableHead>Vendor</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Uploaded</TableHead>
              <TableHead>Rows</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {uploads.map((upload) => (
              <TableRow key={upload.batch_id}>
                <TableCell className="font-medium">{upload.filename}</TableCell>
                <TableCell>{upload.vendor_detected || 'Detecting...'}</TableCell>
                <TableCell>
                  <UploadStatus status={upload.status} />
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {new Date(upload.uploaded_at).toLocaleString()}
                </TableCell>
                <TableCell>
                  {upload.status === 'processing' && upload.total_rows ? (
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{
                            width: `${Math.min(100, Math.round((upload.successful_rows / upload.total_rows) * 100))}%`
                          }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {Math.round((upload.successful_rows / upload.total_rows) * 100)}%
                      </span>
                    </div>
                  ) : upload.total_rows ? (
                    <span className="text-sm">
                      {upload.successful_rows}/{upload.total_rows}
                    </span>
                  ) : (
                    '-'
                  )}
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onViewDetails?.(upload.batch_id)}
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
