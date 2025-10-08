import { useState, useEffect } from 'react'
import { useChatQuery, useChatHistory } from '@/api/chat'
import { MessageList } from '@/components/chat/MessageList'
import { ChatInput } from '@/components/chat/ChatInput'
import { Card } from '@/components/ui/card'
import { EmptyState } from '@/components/ui/empty-state'
import { MessageSquare, Sparkles } from 'lucide-react'
import type { ChatMessage } from '@/types'
import toast from 'react-hot-toast'

export function Chat() {
  const [sessionId, setSessionId] = useState<string>()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const chatQuery = useChatQuery()
  const { data: history } = useChatHistory(sessionId)

  // Load history messages on mount
  useEffect(() => {
    if (history && messages.length === 0 && history.messages.length > 0) {
      setMessages(history.messages)
      setSessionId(history.session_id)
    }
  }, [history, messages.length])

  const handleSend = async (query: string) => {
    // Add user message immediately
    const userMessage: ChatMessage = {
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])

    const loadingToast = toast.loading('AI is thinking...')

    try {
      const response = await chatQuery.mutateAsync({ query, session_id: sessionId })
      setSessionId(response.session_id)

      // Add assistant response
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        sql_generated: response.sql_generated,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMessage])
      toast.success('Response received', { id: loadingToast })
    } catch (error) {
      toast.error('Failed to process your question. Please try again.', { id: loadingToast })
      // Remove user message on error
      setMessages((prev) => prev.slice(0, -1))
    }
  }

  const suggestedQuestions = [
    "What were my top 5 products last month?",
    "Show me total revenue by reseller",
    "Which products have the highest margins?",
    "Compare sales between different regions"
  ]

  return (
    <div className="flex h-[calc(100vh-10rem)] flex-col space-y-6 animate-in fade-in-0 duration-500">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-accent/20 to-primary/20 flex items-center justify-center border border-accent/30 shadow-sm">
          <Sparkles className="h-6 w-6 text-accent" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">AI Chat</h1>
          <p className="text-sm text-muted-foreground mt-1">Ask questions about your sales data in natural language</p>
        </div>
      </div>

      {/* Chat Container */}
      <Card className="flex-1 overflow-hidden border-border bg-card shadow-md">
        <div className="h-full overflow-y-auto p-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center">
              <EmptyState
                icon={MessageSquare}
                title="Start a conversation"
                description="Ask me anything about your sales data, and I'll help you find insights"
              />
              <div className="mt-8 grid gap-3 sm:grid-cols-2 max-w-2xl w-full">
                {suggestedQuestions.map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(question)}
                    className="text-left p-4 rounded-lg border border-border bg-background hover:bg-primary/5 hover:border-primary/50 transition-all duration-200 group shadow-sm"
                  >
                    <div className="flex items-start gap-2">
                      <Sparkles className="h-4 w-4 text-accent mt-0.5 flex-shrink-0" />
                      <p className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">
                        {question}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <MessageList messages={messages} />
          )}
        </div>
      </Card>

      {/* Input */}
      <ChatInput onSend={handleSend} isLoading={chatQuery.isPending} />
    </div>
  )
}
