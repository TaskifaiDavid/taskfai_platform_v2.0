import { useState } from 'react'
import { Upload, Package } from 'lucide-react'
import { BibbiFileUpload } from '@/components/bibbi/BibbiFileUpload'
import { BibbiUploadHistory } from '@/components/bibbi/BibbiUploadHistory'
import { BibbiUploadDetail } from '@/components/bibbi/BibbiUploadDetail'
import { Card } from '@/components/ui/card'

export function BibbiUploads() {
  const [selectedUploadId, setSelectedUploadId] = useState<string | null>(null)

  return (
    <div className="space-y-8 animate-in fade-in-0 duration-500">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-accent/20 to-primary/20 flex items-center justify-center border border-accent/30 shadow-sm">
          <Package className="h-6 w-6 text-accent" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">BIBBI Reseller Uploads</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Upload and manage Excel files from resellers
          </p>
        </div>
      </div>

      {/* Info Card */}
      <Card className="p-6 bg-accent/5 border-accent/20">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 rounded-lg bg-accent/20 flex items-center justify-center flex-shrink-0">
            <Upload className="h-5 w-5 text-accent" />
          </div>
          <div className="space-y-2">
            <h3 className="font-semibold">Supported Resellers</h3>
            <p className="text-sm text-muted-foreground">
              Upload Excel files from: Aromateque, Boxnox, CDLC, Galilu, Liberty,
              Selfridges, Skins NL, Skins SA
            </p>
            <div className="flex flex-wrap gap-2 mt-3">
              <div className="px-3 py-1 bg-background rounded-md text-xs border">
                ✓ Auto vendor detection
              </div>
              <div className="px-3 py-1 bg-background rounded-md text-xs border">
                ✓ Duplicate detection
              </div>
              <div className="px-3 py-1 bg-background rounded-md text-xs border">
                ✓ Auto store creation
              </div>
              <div className="px-3 py-1 bg-background rounded-md text-xs border">
                ✓ 4-layer validation
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Upload Area */}
      <BibbiFileUpload />

      {/* Upload History */}
      <BibbiUploadHistory
        onViewDetails={setSelectedUploadId}
        selectedUploadId={selectedUploadId}
      />

      {/* Upload Detail View */}
      {selectedUploadId && (
        <BibbiUploadDetail
          uploadId={selectedUploadId}
          onClose={() => setSelectedUploadId(null)}
        />
      )}
    </div>
  )
}
