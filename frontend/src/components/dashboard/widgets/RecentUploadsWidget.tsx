import { useUploadsList } from '@/api/uploads'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { Clock, Upload as UploadIcon } from 'lucide-react'
import { UploadStatus } from '@/components/upload/UploadStatus'
import { Skeleton } from '@/components/ui/skeleton'
import { useNavigate } from 'react-router-dom'
import type { WidgetConfig } from '@/types/dashboardConfig'

interface RecentUploadsWidgetProps {
  config: WidgetConfig
}

export function RecentUploadsWidget({ config }: RecentUploadsWidgetProps) {
  const navigate = useNavigate()
  const { data: uploads, isLoading } = useUploadsList()
  const limit = config.props.limit || 5
  const recentUploads = uploads?.slice(0, limit) || []

  return (
    <Card className="border-border bg-card shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="border-b border-border bg-background/50">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <div className="h-8 w-8 rounded-lg bg-accent/10 flex items-center justify-center">
                <Clock className="h-4 w-4 text-accent" />
              </div>
              {config.props.title || 'Recent Uploads'}
            </CardTitle>
            <CardDescription className="mt-1.5">
              {config.props.description || 'Latest file uploads and processing status'}
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/uploads')}
            className="hover:bg-accent/10 hover:text-accent"
          >
            View all
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="space-y-3">
          {isLoading ? (
            <>
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full bg-muted" />
              ))}
            </>
          ) : recentUploads.length > 0 ? (
            recentUploads.map((upload) => (
              <div
                key={upload.batch_id}
                className="flex items-center justify-between rounded-lg border border-border p-4 hover:bg-background/80 hover:border-primary/50 transition-all duration-200 group cursor-pointer"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold truncate group-hover:text-primary transition-colors">
                    {upload.filename}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(upload.uploaded_at).toLocaleString()}
                  </p>
                </div>
                <UploadStatus status={upload.status} />
              </div>
            ))
          ) : (
            <EmptyState
              icon={UploadIcon}
              title="No uploads yet"
              description="Upload your first file to get started with analytics"
              action={{
                label: "Go to Uploads",
                onClick: () => navigate('/uploads')
              }}
            />
          )}
        </div>
      </CardContent>
    </Card>
  )
}
