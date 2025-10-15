import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useQueryClient } from '@tanstack/react-query'
import { useUploadFile } from '@/api/uploads'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Upload, FileSpreadsheet, Loader2, X, Trash2 } from 'lucide-react'
import { useUIStore } from '@/stores/ui'
import { cn } from '@/lib/utils'

interface QueuedFile {
  file: File
  id: string
}

export function FileUpload() {
  const [fileQueue, setFileQueue] = useState<QueuedFile[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const queryClient = useQueryClient()
  const uploadFile = useUploadFile()
  const addNotification = useUIStore((state) => state.addNotification)

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return

      // Add files to queue instead of immediately uploading
      const newFiles = acceptedFiles.map((file) => ({
        file,
        id: `${file.name}-${Date.now()}-${Math.random()}`,
      }))
      setFileQueue((prev) => [...prev, ...newFiles])

      addNotification({
        type: 'info',
        title: 'Files queued',
        message: `${acceptedFiles.length} file(s) added to upload queue`,
      })
    },
    [addNotification]
  )

  const removeFile = (id: string) => {
    setFileQueue((prev) => prev.filter((qf) => qf.id !== id))
  }

  const clearQueue = () => {
    setFileQueue([])
  }

  const uploadAll = async () => {
    if (fileQueue.length === 0) return

    setIsUploading(true)

    // Upload all files in parallel instead of sequentially
    const uploadPromises = fileQueue.map((queuedFile) =>
      uploadFile
        .mutateAsync({ file: queuedFile.file, mode: 'append' })
        .then(() => ({ success: true, filename: queuedFile.file.name }))
        .catch((error) => ({ success: false, filename: queuedFile.file.name, error }))
    )

    const results = await Promise.all(uploadPromises)
    const successCount = results.filter((r) => r.success).length
    const failCount = results.filter((r) => !r.success).length

    setIsUploading(false)
    setFileQueue([])

    if (successCount > 0) {
      // Invalidate queries to refresh dashboard and upload list
      queryClient.invalidateQueries({ queryKey: ['kpis'] })
      queryClient.invalidateQueries({ queryKey: ['uploads'] })

      addNotification({
        type: 'success',
        title: 'Upload complete',
        message: `${successCount} file(s) uploaded successfully${failCount > 0 ? `, ${failCount} failed` : ''}`,
      })
    }

    if (failCount > 0 && successCount === 0) {
      addNotification({
        type: 'error',
        title: 'Upload failed',
        message: `Failed to upload ${failCount} file(s). Please try again.`,
      })
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    multiple: true,
    disabled: isUploading,
  })

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="space-y-4">
      <Card className="glass border-white/5 elevation-2">
        <CardContent className="pt-6">
          <div
            {...getRootProps()}
            className={cn(
              'flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-all duration-300',
              isDragActive && 'border-primary bg-primary/5 scale-[1.02]',
              !isDragActive && 'border-white/10 hover:border-primary/50 hover:bg-white/5',
              isUploading && 'opacity-50 cursor-not-allowed'
            )}
          >
            <input {...getInputProps()} />
            {isUploading ? (
              <div className="text-center animate-in fade-in-0 zoom-in-95">
                <Loader2 className="mb-4 h-12 w-12 animate-spin text-primary mx-auto" />
                <p className="text-lg font-medium">Uploading...</p>
                <p className="text-sm text-muted-foreground mt-1">Processing your files</p>
              </div>
            ) : (
              <div className="text-center animate-in fade-in-0 zoom-in-95">
                <div className="h-16 w-16 rounded-xl bg-accent/10 flex items-center justify-center mx-auto mb-4 group-hover:bg-accent/20 transition-colors">
                  <FileSpreadsheet className="h-8 w-8 text-accent" />
                </div>
                <p className="mb-2 text-lg font-medium">
                  {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
                </p>
                <p className="mb-4 text-sm text-muted-foreground">
                  Supports CSV, XLS, and XLSX files (max 50MB each)
                </p>
                <Button className="shadow-lg hover:shadow-xl transition-shadow">
                  <Upload className="mr-2 h-4 w-4" />
                  Choose Files
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {fileQueue.length > 0 && (
        <Card className="glass border-white/5 elevation-2">
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">
                  Upload Queue ({fileQueue.length})
                </h3>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearQueue}
                    disabled={isUploading}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Clear All
                  </Button>
                  <Button
                    onClick={uploadAll}
                    disabled={isUploading}
                    className="shadow-lg hover:shadow-xl transition-shadow"
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Upload All
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                {fileQueue.map((qf) => (
                  <div
                    key={qf.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <FileSpreadsheet className="h-5 w-5 text-accent flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{qf.file.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {formatFileSize(qf.file.size)}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFile(qf.id)}
                      disabled={isUploading}
                      className="flex-shrink-0"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
