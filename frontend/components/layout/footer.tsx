import { footerNav, siteConfig } from "@/config/site"
import { ApiStatus } from "@/components/layout/api-status"
import { Logo } from "@/components/layout/logo"

export function Footer() {
  const year = new Date().getFullYear()

  return (
    <footer className="border-t-2 border-hairline bg-cloud">
      <div className="container-page py-14">
        <div className="grid gap-10 md:grid-cols-[1.6fr_1fr_1fr]">
          <div className="max-w-sm">
            <Logo />
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              structured savings and a readable credit record for people whose income
              does not arrive as a monthly salary.
            </p>
            <a
              href={`mailto:${siteConfig.contactEmail}`}
              className="mt-4 inline-block text-sm font-bold text-link hover:underline"
            >
              {siteConfig.contactEmail}
            </a>
          </div>

          {footerNav.map((group) => (
            <div key={group.title}>
              <h3 className="text-xs font-extrabold tracking-wider text-muted-foreground/80">
                {group.title}
              </h3>
              <ul className="mt-4 flex flex-col gap-3">
                {group.links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-sm font-semibold text-foreground/80 transition-colors hover:text-link"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col gap-3 border-t border-hairline pt-6 text-xs font-semibold text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <p>© {year} sura. all rights reserved.</p>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
            <ApiStatus />
            <span>sura never holds customer funds.</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
