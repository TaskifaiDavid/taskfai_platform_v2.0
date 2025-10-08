import { useUploadErrors } from '@/api/uploads'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AlertCircle, Loader2 } from 'lucide-react'

interface ErrorReportProps {
  batchId: string
}

export function ErrorReport({ batchId }: ErrorReportProps) {
  const { data: errors, isLoading } = useUploadErrors(batchId)

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (!errors || errors.length === 0) {
    return null
  }

  return (
    <Card className="border-destructive">
      <CardHeader>
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <CardTitle className="text-destructive">Processing Errors</CardTitle>
        </div>
        <CardDescription>{errors.length} rows failed to process</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Row #</TableHead>
              <TableHead>Error Message</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {errors.map((error, idx) => (
              <TableRow key={idx}>
                <TableCell className="font-mono">{error.row_number}</TableCell>
                <TableCell className="text-sm text-destructive">{error.error_message}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
