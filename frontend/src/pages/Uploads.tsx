import { useState } from 'react'
import { FileUpload } from '@/components/upload/FileUpload'
import { UploadHistory } from '@/components/upload/UploadHistory'
import { ErrorReport } from '@/components/upload/ErrorReport'
import { Upload } from 'lucide-react'

export function Uploads() {
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null)

  return (
    <div className="space-y-8 animate-in fade-in-0 duration-500">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-accent/20 to-primary/20 flex items-center justify-center border border-accent/30 shadow-sm">
          <Upload className="h-6 w-6 text-accent" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">File Uploads</h1>
          <p className="text-sm text-muted-foreground mt-1">Upload and manage vendor sales data files</p>
        </div>
      </div>

      {/* Upload Area */}
      <FileUpload />

      {/* Upload History */}
      <UploadHistory onViewDetails={setSelectedBatchId} />

      {/* Error Report */}
      {selectedBatchId && <ErrorReport batchId={selectedBatchId} />}
    </div>
  )
}
