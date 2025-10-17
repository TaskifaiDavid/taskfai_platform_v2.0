import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useBibbiUploadFile, useBibbiResellers } from '@/api/bibbi'

export function BibbiFileUpload() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedReseller, setSelectedReseller] = useState<string>('')
  const uploadMutation = useBibbiUploadFile()
  const { data: resellersData, isLoading: isLoadingResellers } = useBibbiResellers()

  // Mock resellers for now since endpoint doesn't exist yet
  const mockResellers = [
    { reseller_id: 'aromat', reseller_name: 'Aromateque' },
    { reseller_id: 'boxnox', reseller_name: 'Boxnox' },
    { reseller_id: 'cdlc', reseller_name: 'CDLC (Creme de la Creme)' },
    { reseller_id: 'galilu', reseller_name: 'Galilu' },
    { reseller_id: 'liberty', reseller_name: 'Liberty' },
    { reseller_id: 'selfridges', reseller_name: 'Selfridges' },
    { reseller_id: 'skins_nl', reseller_name: 'Skins NL' },
    { reseller_id: 'skins_sa', reseller_name: 'Skins SA' },
  ]

  const resellers = resellersData || mockResellers

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
    multiple: false,
  })

  const handleUpload = async () => {
    if (!selectedFile || !selectedReseller) return

    try {
      await uploadMutation.mutateAsync({
        file: selectedFile,
        reseller_id: selectedReseller,
      })

      // Reset form on success
      setSelectedFile(null)
      setSelectedReseller('')
    } catch (error) {
      console.error('Upload failed:', error)
    }
  }

  const handleRemoveFile = () => {
    setSelectedFile(null)
  }

  return (
    <Card className="p-6">
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold mb-2">Upload Reseller File</h2>
          <p className="text-sm text-muted-foreground">
            Select a reseller and upload their Excel sales data file
          </p>
        </div>

        {/* Reseller Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Select Reseller</label>
          <select
            value={selectedReseller}
            onChange={(e) => setSelectedReseller(e.target.value)}
            className="w-full p-3 border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={uploadMutation.isPending}
          >
            <option value="">Choose a reseller...</option>
            {resellers.map((reseller) => (
              <option key={reseller.reseller_id} value={reseller.reseller_id}>
                {reseller.reseller_name}
              </option>
            ))}
          </select>
        </div>

        {/* File Upload Area */}
        {!selectedFile ? (
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-primary bg-primary/5'
                : 'border-muted-foreground/25 hover:border-primary/50'
            }`}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center gap-4">
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                <Upload className="h-8 w-8 text-primary" />
              </div>
              <div className="space-y-2">
                <p className="text-lg font-medium">
                  {isDragActive ? 'Drop file here' : 'Drop Excel file here or click to browse'}
                </p>
                <p className="text-sm text-muted-foreground">
                  Supported formats: .xlsx, .xls (max 50MB)
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="border rounded-lg p-4 bg-accent/5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <File className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRemoveFile}
                disabled={uploadMutation.isPending}
              >
                Remove
              </Button>
            </div>
          </div>
        )}

        {/* Upload Button */}
        <Button
          onClick={handleUpload}
          disabled={!selectedFile || !selectedReseller || uploadMutation.isPending}
          className="w-full"
          size="lg"
        >
          {uploadMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="mr-2 h-4 w-4" />
              Upload File
            </>
          )}
        </Button>

        {/* Success Message */}
        {uploadMutation.isSuccess && (
          <Alert className="bg-green-500/10 border-green-500/50">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <AlertDescription className="text-green-700 dark:text-green-400">
              File uploaded successfully! Processing will begin shortly.
            </AlertDescription>
          </Alert>
        )}

        {/* Error Message */}
        {uploadMutation.isError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Upload failed: {uploadMutation.error?.message || 'Unknown error'}
            </AlertDescription>
          </Alert>
        )}
      </div>
    </Card>
  )
}
