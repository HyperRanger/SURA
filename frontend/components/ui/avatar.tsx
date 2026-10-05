"use client"

import { Avatar as AvatarPrimitive } from "@base-ui/react/avatar"
import { cn } from "@/lib/utils"

function Avatar({ className, ...props }: AvatarPrimitive.Root.Props) {
  return (
    <AvatarPrimitive.Root
      data-slot="avatar"
      className={cn(
        "relative inline-flex size-10 shrink-0 items-center justify-center overflow-hidden rounded-full border-2 border-hairline bg-indigo-soft align-middle select-none",
        className
      )}
      {...props}
    />
  )
}

function AvatarImage({ className, ...props }: AvatarPrimitive.Image.Props) {
  return <AvatarPrimitive.Image data-slot="avatar-image" className={cn("size-full object-cover", className)} {...props} />
}

function AvatarFallback({ className, ...props }: AvatarPrimitive.Fallback.Props) {
  return (
    <AvatarPrimitive.Fallback
      data-slot="avatar-fallback"
      className={cn("flex size-full items-center justify-center text-sm font-black text-link", className)}
      {...props}
    />
  )
}

// a stable cartoon face per seed from dicebear. the seed is hashed first so
// internal ids never leave the browser
export function dicebearUrl(seed: string, style = "notionists-neutral") {
  let hash = 0
  for (const char of seed) hash = (Math.imul(31, hash) + char.charCodeAt(0)) | 0
  const params = new URLSearchParams({ seed: (hash >>> 0).toString(36), backgroundColor: "e7e5f2,f6e7c1" })
  return `https://api.dicebear.com/9.x/${style}/svg?${params}`
}

export { Avatar, AvatarFallback, AvatarImage }
