import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import type { ChatQueryRequest, ChatQueryResponse, Conversation } from '@/types'

export function useChatQuery() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: ChatQueryRequest) =>
      apiClient.post<ChatQueryResponse>('/api/chat/query', request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-history'] })
    },
  })
}

export function useChatHistory(sessionId?: string) {
  return useQuery({
    queryKey: ['chat-history', sessionId],
    queryFn: () => apiClient.get<Conversation>(`/api/chat/history${sessionId ? `?session_id=${sessionId}` : ''}`),
  })
}

export function useClearHistory() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => apiClient.delete('/api/chat/history'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-history'] })
    },
  })
}
