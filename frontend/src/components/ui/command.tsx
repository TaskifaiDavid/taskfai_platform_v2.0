import * as React from "react"
import { Search } from "lucide-react"
import { cn } from "@/lib/utils"
import { Dialog, DialogContent } from "./dialog"

export interface CommandItem {
  value: string
  label: string
  icon?: React.ReactNode
  onSelect?: () => void
  keywords?: string[]
}

export interface CommandGroup {
  heading?: string
  items: CommandItem[]
}

export interface CommandProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  groups: CommandGroup[]
  placeholder?: string
}

export function Command({
  open,
  onOpenChange,
  groups,
  placeholder = "Type a command or search...",
}: CommandProps) {
  const [search, setSearch] = React.useState("")
  const [selectedIndex, setSelectedIndex] = React.useState(0)

  const filteredGroups = React.useMemo(() => {
    if (!search) return groups

    return groups
      .map((group) => ({
        ...group,
        items: group.items.filter((item) => {
          const searchLower = search.toLowerCase()
          const matchesLabel = item.label.toLowerCase().includes(searchLower)
          const matchesValue = item.value.toLowerCase().includes(searchLower)
          const matchesKeywords = item.keywords?.some((keyword) =>
            keyword.toLowerCase().includes(searchLower)
          )
          return matchesLabel || matchesValue || matchesKeywords
        }),
      }))
      .filter((group) => group.items.length > 0)
  }, [groups, search])

  const allItems = React.useMemo(
    () => filteredGroups.flatMap((group) => group.items),
    [filteredGroups]
  )

  React.useEffect(() => {
    setSelectedIndex(0)
  }, [search])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setSelectedIndex((prev) => (prev + 1) % allItems.length)
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setSelectedIndex((prev) => (prev - 1 + allItems.length) % allItems.length)
    } else if (e.key === "Enter") {
      e.preventDefault()
      const selected = allItems[selectedIndex]
      if (selected) {
        selected.onSelect?.()
        onOpenChange(false)
        setSearch("")
      }
    }
  }

  React.useEffect(() => {
    if (!open) {
      setSearch("")
      setSelectedIndex(0)
    }
  }, [open])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-2xl p-0 overflow-hidden"
        onClose={() => onOpenChange(false)}
        showCloseButton={false}
      >
        <div className="flex items-center border-b px-3" onKeyDown={handleKeyDown}>
          <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
          <input
            className={cn(
              "flex h-11 w-full rounded-md bg-transparent py-3 text-sm outline-none",
              "placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
            )}
            placeholder={placeholder}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            autoFocus
          />
        </div>

        <div className="max-h-[300px] overflow-y-auto overflow-x-hidden p-2">
          {filteredGroups.length === 0 ? (
            <div className="py-6 text-center text-sm text-muted-foreground">
              No results found.
            </div>
          ) : (
            filteredGroups.map((group, groupIndex) => (
              <div key={groupIndex} className="mb-2 last:mb-0">
                {group.heading && (
                  <div className="px-2 py-1.5 text-xs font-medium text-muted-foreground">
                    {group.heading}
                  </div>
                )}
                <div className="space-y-1">
                  {group.items.map((item, itemIndex) => {
                    const globalIndex = filteredGroups
                      .slice(0, groupIndex)
                      .reduce((acc, g) => acc + g.items.length, 0) + itemIndex
                    const isSelected = globalIndex === selectedIndex

                    return (
                      <button
                        key={item.value}
                        className={cn(
                          "relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none",
                          "transition-colors",
                          isSelected
                            ? "bg-accent text-accent-foreground"
                            : "hover:bg-accent hover:text-accent-foreground"
                        )}
                        onClick={() => {
                          item.onSelect?.()
                          onOpenChange(false)
                          setSearch("")
                        }}
                        onMouseEnter={() => setSelectedIndex(globalIndex)}
                      >
                        {item.icon && (
                          <div className="mr-2 h-4 w-4">{item.icon}</div>
                        )}
                        <span>{item.label}</span>
                      </button>
                    )
                  })}
                </div>
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
