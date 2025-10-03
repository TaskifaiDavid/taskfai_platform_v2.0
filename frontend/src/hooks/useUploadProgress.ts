import { useState, useEffect, useCallback } from 'react';

interface UploadBatch {
  batch_id: string;
  filename: string;
  file_size: number;
  upload_mode: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  uploaded_at: string;
  processed_at?: string;
  total_rows?: number;
  successful_rows?: number;
  failed_rows?: number;
  error_message?: string;
  detected_vendor?: string;
}

interface UseUploadProgressOptions {
  batchId: string;
  pollingInterval?: number;
  autoStop?: boolean;
}

export function useUploadProgress({
  batchId,
  pollingInterval = 5000,
  autoStop = true,
}: UseUploadProgressOptions) {
  const [batch, setBatch] = useState<UploadBatch | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(true);

  const fetchBatchStatus = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(
        `http://localhost:8000/api/uploads/batches/${batchId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch batch status');
      }

      const result = await response.json();
      setBatch(result.batch);
      setLoading(false);

      // Auto-stop polling if processing is complete or failed
      if (
        autoStop &&
        (result.batch.processing_status === 'completed' ||
          result.batch.processing_status === 'failed')
      ) {
        setIsPolling(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status');
      setLoading(false);
    }
  }, [batchId, autoStop]);

  useEffect(() => {
    if (!isPolling) return;

    // Fetch immediately
    fetchBatchStatus();

    // Set up polling
    const interval = setInterval(fetchBatchStatus, pollingInterval);

    return () => clearInterval(interval);
  }, [fetchBatchStatus, isPolling, pollingInterval]);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
  }, []);

  const startPolling = useCallback(() => {
    setIsPolling(true);
  }, []);

  const getProgressPercentage = useCallback(() => {
    if (!batch) return 0;

    switch (batch.processing_status) {
      case 'pending':
        return 0;
      case 'processing':
        if (batch.total_rows && batch.successful_rows !== undefined) {
          return Math.round(
            ((batch.successful_rows + (batch.failed_rows || 0)) /
              batch.total_rows) *
              100
          );
        }
        return 50; // Default to 50% if no row counts available
      case 'completed':
        return 100;
      case 'failed':
        return 100;
      default:
        return 0;
    }
  }, [batch]);

  return {
    batch,
    loading,
    error,
    isPolling,
    stopPolling,
    startPolling,
    refresh: fetchBatchStatus,
    progressPercentage: getProgressPercentage(),
  };
}

export function useUploadHistory(
  options: {
    limit?: number;
    status?: string;
  } = {}
) {
  const { limit = 20, status } = options;
  const [batches, setBatches] = useState<UploadBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBatches = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const params = new URLSearchParams({
        limit: limit.toString(),
      });

      if (status) {
        params.append('status', status);
      }

      const response = await fetch(
        `http://localhost:8000/api/uploads/batches?${params}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch upload history');
      }

      const result = await response.json();
      setBatches(result.batches);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch history');
      setLoading(false);
    }
  }, [limit, status]);

  useEffect(() => {
    fetchBatches();
  }, [fetchBatches]);

  return {
    batches,
    loading,
    error,
    refresh: fetchBatches,
  };
}
