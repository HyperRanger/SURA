"use client"

import { useState } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { Menu01Icon } from "@hugeicons/core-free-icons"
import Link from "next/link"
import { routes } from "@/config/routes"
import { mainNav } from "@/config/site"
import { buttonVariants } from "@/components/ui/button"
import { Logo } from "@/components/layout/logo"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"

export function MobileNav() {
  const [open, setOpen] = useState(false)
  const close = () => setOpen(false)

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        aria-label="open menu"
        className="flex size-10 items-center justify-center rounded-full border-2 border-hairline text-foreground transition-colors hover:border-link hover:text-link"
      >
        <HugeiconsIcon icon={Menu01Icon} size={20} strokeWidth={2} />
      </SheetTrigger>

      <SheetContent side="right" className="w-full max-w-sm gap-0 lowercase">
        <SheetHeader className="p-5">
          <SheetTitle render={<div />}>
            <Logo />
          </SheetTitle>
          <SheetDescription className="sr-only">site navigation</SheetDescription>
        </SheetHeader>

        <nav aria-label="mobile" className="flex flex-col gap-1 px-3">
          {mainNav.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={close}
              className="rounded-full px-4 py-3 text-lg font-bold text-foreground transition-colors hover:bg-cloud hover:text-link"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="mt-auto flex flex-col gap-3 p-5">
          <Link
            href={routes.login}
            onClick={close}
            className={buttonVariants({ variant: "outline", className: "w-full" })}
          >
            log in
          </Link>
          <Link
            href={routes.signup}
            onClick={close}
            className={buttonVariants({ className: "w-full" })}
          >
            get started
          </Link>
        </div>
      </SheetContent>
    </Sheet>
  )
}
