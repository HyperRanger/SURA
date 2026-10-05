"use client"

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
        "flex shrink-0 items-center gap-2 rounded-t-xl px-3 pt-2 pb-3 text-sm font-extrabold whitespace-nowrap text-muted-foreground transition-colors outline-none",
        "hover:text-link focus-visible:ring-4 focus-visible:ring-ring/20 data-active:text-link",
        className
      )}
      {...props}
    />
  )
}

function TabsPanel({ className, ...props }: TabsPrimitive.Panel.Props) {
  return <TabsPrimitive.Panel data-slot="tabs-panel" className={cn("pt-6 outline-none sm:pt-8", className)} {...props} />
}

export { Tabs, TabsList, TabsPanel, TabsTab }
