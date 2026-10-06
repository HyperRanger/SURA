import Link from "next/link"
import { footerLinks } from "@/config/site"
import { Logo } from "@/components/layout/logo"

export function PublicFooter() {
  const year = new Date().getFullYear()

  return (
    <footer className="border-t-2 border-hairline bg-card">
      <div className="container-app py-10 pb-[max(2.5rem,env(safe-area-inset-bottom))]">
        <div className="flex flex-col gap-8 md:flex-row md:items-start md:justify-between">
          <div className="max-w-xs">
            <Logo />
            <p className="mt-3 text-sm leading-relaxed font-semibold text-muted-foreground">
              Sura never holds your money. Your funds stay with the bank or fintech that offers Sura to you.
            </p>
          </div>

          <nav aria-label="Footer">
            <ul className="grid grid-cols-2 gap-x-8 gap-y-3 sm:grid-cols-3">
              {footerLinks.map((link) => (
                <li key={link.label}>
                  <Link href={link.href} className="text-sm font-bold text-muted-foreground transition-colors hover:text-link">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <p className="mt-10 border-t-2 border-dashed border-hairline pt-6 text-xs font-semibold text-muted-foreground">
          © {year} Sura. All rights reserved.
        </p>
      </div>
    </footer>
  )
}
