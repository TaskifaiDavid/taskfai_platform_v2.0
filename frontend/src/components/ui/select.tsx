import * as React from "react"
import { ChevronDown, Check } from "lucide-react"
import { cn } from "@/lib/utils"

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface SelectProps {
  options: SelectOption[]
  value?: string
  onValueChange?: (value: string) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}

export function Select({
  options,
  value,
  onValueChange,
  placeholder = "Select an option",
  disabled = false,
  className,
}: SelectProps) {
  const [isOpen, setIsOpen] = React.useState(false)
  const selectRef = React.useRef<HTMLDivElement>(null)

  const selectedOption = options.find((opt) => opt.value === value)

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside)
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [isOpen])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return

    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      setIsOpen(!isOpen)
    } else if (e.key === "Escape") {
      setIsOpen(false)
    } else if (e.key === "ArrowDown" && isOpen) {
      e.preventDefault()
      const currentIndex = options.findIndex((opt) => opt.value === value)
      const nextIndex = currentIndex + 1 < options.length ? currentIndex + 1 : 0
      onValueChange?.(options[nextIndex].value)
    } else if (e.key === "ArrowUp" && isOpen) {
      e.preventDefault()
      const currentIndex = options.findIndex((opt) => opt.value === value)
      const prevIndex = currentIndex - 1 >= 0 ? currentIndex - 1 : options.length - 1
      onValueChange?.(options[prevIndex].value)
    }
  }

  return (
    <div ref={selectRef} className={cn("relative w-full", className)}>
      <button
        type="button"
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        disabled={disabled}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        className={cn(
          "flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "hover:bg-accent/50 transition-colors"
        )}
      >
        <span className={cn(!selectedOption && "text-muted-foreground")}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDown
          className={cn(
            "h-4 w-4 opacity-50 transition-transform",
            isOpen && "rotate-180"
          )}
        />
      </button>

      {isOpen && (
        <div
          role="listbox"
          className={cn(
            "absolute z-50 mt-1 w-full min-w-[8rem] overflow-hidden rounded-md border bg-popover shadow-md",
            "animate-in fade-in-0 zoom-in-95"
          )}
        >
          <div className="max-h-[300px] overflow-auto p-1">
            {options.map((option) => (
              <button
                key={option.value}
                type="button"
                role="option"
                aria-selected={value === option.value}
                disabled={option.disabled}
                onClick={() => {
                  if (!option.disabled) {
                    onValueChange?.(option.value)
                    setIsOpen(false)
                  }
                }}
                className={cn(
                  "relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none",
                  "focus:bg-accent focus:text-accent-foreground",
                  "hover:bg-accent hover:text-accent-foreground",
                  "disabled:pointer-events-none disabled:opacity-50",
                  value === option.value && "bg-accent"
                )}
              >
                {value === option.value && (
                  <Check className="absolute left-2 h-4 w-4" />
                )}
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
