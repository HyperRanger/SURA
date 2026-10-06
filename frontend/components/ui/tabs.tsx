"use client"

import type * as React from "react"
import { Tabs as TabsPrimitive } from "@base-ui/react/tabs"
import { cn } from "@/lib/utils"

function Tabs({ className, ...props }: TabsPrimitive.Root.Props) {
  return <TabsPrimitive.Root data-slot="tabs" className={cn("flex flex-col", className)} {...props} />
}

// an underlined row that scrolls sideways on phones rather than wrapping
function TabsList({ className, children, ...props }: TabsPrimitive.List.Props) {
  return (
    <TabsPrimitive.List
      data-slot="tabs-list"
      className={cn(
        "relative flex gap-1 overflow-x-auto border-b-2 border-hairline [scrollbar-width:none] [&::-webkit-scrollbar]:hidden",
        className
      )}
      {...props}
    >
      {children}
      <TabsPrimitive.Indicator
        data-slot="tabs-indicator"
        className="absolute bottom-[-2px] left-0 h-[3px] w-(--active-tab-width) translate-x-(--active-tab-left) rounded-full bg-link transition-all duration-200 ease-out"
      />
    </TabsPrimitive.List>
  )
}

function TabsTab({ className, ...props }: TabsPrimitive.Tab.Props) {
  return (
    <TabsPrimitive.Tab
      data-slot="tabs-tab"
      className={cn(
        "group/tab flex shrink-0 cursor-pointer items-center gap-2 rounded-t-xl px-3 pt-2 pb-3 text-sm font-extrabold whitespace-nowrap text-muted-foreground transition-colors outline-none",
        "hover:text-link focus-visible:ring-4 focus-visible:ring-ring/20 data-active:text-link",
        className
      )}
      {...props}
    />
  )
}

// a small count beside a tab label, e.g. how many members a commitment has
function TabsCount({ children, alert, className }: { children: React.ReactNode; alert?: boolean; className?: string }) {
  return (
    <span
      className={cn(
        "flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-[0.7rem] font-black tabular-nums",
        alert ? "bg-destructive text-white" : "bg-cloud text-muted-foreground group-data-active/tab:bg-indigo-soft group-data-active/tab:text-link",
        className
      )}
    >
      {children}
    </span>
  )
}

function TabsPanel({ className, ...props }: TabsPrimitive.Panel.Props) {
  return <TabsPrimitive.Panel data-slot="tabs-panel" className={cn("pt-6 outline-none sm:pt-8", className)} {...props} />
}

export { Tabs, TabsCount, TabsList, TabsPanel, TabsTab }
