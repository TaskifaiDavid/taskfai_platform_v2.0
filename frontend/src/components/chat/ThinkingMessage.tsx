import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Bot, Search, Brain, Zap, BarChart3, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

const THINKING_STAGES = [
  { icon: Search, text: 'Analyzing your question...', color: 'text-blue-500' },
  { icon: Brain, text: 'Understanding data requirements...', color: 'text-purple-500' },
  { icon: Zap, text: 'Generating SQL query...', color: 'text-yellow-500' },
  { icon: BarChart3, text: 'Fetching results...', color: 'text-green-500' },
  { icon: Sparkles, text: 'Formatting response...', color: 'text-pink-500' },
]

export function ThinkingMessage() {
  const [currentStage, setCurrentStage] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStage((prev) => (prev + 1) % THINKING_STAGES.length)
    }, 1500)

    return () => clearInterval(interval)
  }, [])

  const stage = THINKING_STAGES[currentStage]
  const StageIcon = stage.icon

  return (
    <div className="flex gap-3 animate-in fade-in-0 duration-300">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary">
        <Bot className="h-4 w-4 text-secondary-foreground" />
      </div>
      <Card className="max-w-[80%] p-4 bg-secondary/50 border-secondary">
        <div className="flex items-center gap-3">
          <div className="relative">
            <StageIcon className={cn('h-5 w-5 animate-pulse', stage.color)} />
            <div className="absolute inset-0 animate-ping opacity-75">
              <StageIcon className={cn('h-5 w-5', stage.color)} />
            </div>
          </div>
          <span className="text-sm text-muted-foreground animate-pulse">
            {stage.text}
          </span>
        </div>
        <div className="mt-3 flex gap-1">
          {THINKING_STAGES.map((_, idx) => (
            <div
              key={idx}
              className={cn(
                'h-1 flex-1 rounded-full transition-all duration-300',
                idx === currentStage ? 'bg-accent' : 'bg-muted'
              )}
            />
          ))}
        </div>
      </Card>
    </div>
  )
}
