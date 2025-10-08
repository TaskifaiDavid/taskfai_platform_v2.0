import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { useExportReport, useDownloadReport } from '@/api/analytics'
import type { ExportRequest } from '@/types'
import { Download, FileText, FileSpreadsheet, Loader2 } from 'lucide-react'
import { useUIStore } from '@/stores/ui'

interface ExportButtonProps {
  dateFrom: string
  dateTo: string
}

export function ExportButton({ dateFrom, dateTo }: ExportButtonProps) {
  const [taskId, setTaskId] = useState<string | null>(null)
  const exportReport = useExportReport()
  const { data: exportStatus } = useDownloadReport(taskId)
  const addNotification = useUIStore((state) => state.addNotification)

  const handleExport = async (format: ExportRequest['format']) => {
    try {
      const result = await exportReport.mutateAsync({
        format,
        date_from: dateFrom,
        date_to: dateTo,
      })
      setTaskId(result.task_id)
      addNotification({
        type: 'info',
        title: 'Export started',
        message: `Generating ${format.toUpperCase()} report...`,
      })
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Export failed',
        message: 'Failed to generate report',
      })
    }
  }

  // Auto-download when ready
  if (exportStatus?.status === 'completed' && exportStatus.download_url) {
    window.open(exportStatus.download_url, '_blank')
    setTaskId(null)
  }

  const isExporting = taskId && exportStatus?.status === 'processing'

  return (
    <div className="flex gap-2">
      <Button
        variant="outline"
        onClick={() => handleExport('pdf')}
        disabled={isExporting || !dateFrom || !dateTo}
      >
        {isExporting ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <FileText className="mr-2 h-4 w-4" />
        )}
        PDF
      </Button>
      <Button
        variant="outline"
        onClick={() => handleExport('csv')}
        disabled={isExporting || !dateFrom || !dateTo}
      >
        {isExporting ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <FileSpreadsheet className="mr-2 h-4 w-4" />
        )}
        CSV
      </Button>
      <Button
        variant="outline"
        onClick={() => handleExport('excel')}
        disabled={isExporting || !dateFrom || !dateTo}
      >
        {isExporting ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Download className="mr-2 h-4 w-4" />
        )}
        Excel
      </Button>
    </div>
  )
}
