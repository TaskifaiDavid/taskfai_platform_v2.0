import { useEffect, useRef } from 'react'
import { Message } from './Message'
import { ThinkingMessage } from './ThinkingMessage'
import type { ChatMessage } from '@/types'

interface MessageListProps {
  messages: ChatMessage[]
  isThinking?: boolean
}

export function MessageList({ messages, isThinking }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isThinking])

  if (messages.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center">
          <p className="text-lg font-medium">No messages yet</p>
          <p className="text-sm">Start a conversation by asking a question</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {messages.map((message, idx) => (
        <Message key={idx} message={message} />
      ))}
      {isThinking && <ThinkingMessage />}
      <div ref={messagesEndRef} />
    </div>
  )
}
