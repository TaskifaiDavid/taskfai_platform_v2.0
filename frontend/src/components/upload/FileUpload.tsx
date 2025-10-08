import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useUploadFile } from '@/api/uploads'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Upload, FileSpreadsheet, Loader2 } from 'lucide-react'
import { useUIStore } from '@/stores/ui'
import { cn } from '@/lib/utils'

export function FileUpload() {
  const uploadFile = useUploadFile()
  const addNotification = useUIStore((state) => state.addNotification)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return

      const file = acceptedFiles[0]
      try {
        await uploadFile.mutateAsync({ file, mode: 'append' })
        addNotification({
          type: 'success',
          title: 'Upload started',
          message: `Processing ${file.name}...`,
        })
      } catch (error) {
        addNotification({
          type: 'error',
          title: 'Upload failed',
          message: 'Failed to upload file. Please try again.',
        })
      }
    },
    [uploadFile, addNotification]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxFiles: 1,
    disabled: uploadFile.isPending,
  })

  return (
    <Card className="glass border-white/5 elevation-2">
      <CardContent className="pt-6">
        <div
          {...getRootProps()}
          className={cn(
            'flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-all duration-300',
            isDragActive && 'border-primary bg-primary/5 scale-[1.02]',
            !isDragActive && 'border-white/10 hover:border-primary/50 hover:bg-white/5',
            uploadFile.isPending && 'opacity-50 cursor-not-allowed'
          )}
        >
          <input {...getInputProps()} />
          {uploadFile.isPending ? (
            <div className="text-center animate-in fade-in-0 zoom-in-95">
              <Loader2 className="mb-4 h-12 w-12 animate-spin text-primary mx-auto" />
              <p className="text-lg font-medium">Uploading...</p>
              <p className="text-sm text-muted-foreground mt-1">Processing your file</p>
            </div>
          ) : (
            <div className="text-center animate-in fade-in-0 zoom-in-95">
              <div className="h-16 w-16 rounded-xl bg-accent/10 flex items-center justify-center mx-auto mb-4 group-hover:bg-accent/20 transition-colors">
                <FileSpreadsheet className="h-8 w-8 text-accent" />
              </div>
              <p className="mb-2 text-lg font-medium">
                {isDragActive ? 'Drop file here' : 'Drag & drop a file here'}
              </p>
              <p className="mb-4 text-sm text-muted-foreground">
                Supports CSV, XLS, and XLSX files (max 50MB)
              </p>
              <Button className="shadow-lg hover:shadow-xl transition-shadow">
                <Upload className="mr-2 h-4 w-4" />
                Choose File
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
