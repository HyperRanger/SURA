import type { Metadata, Viewport } from "next"
import { Nunito } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { ThemeProvider } from "next-themes"
import { siteConfig } from "@/config/site"
import "./globals.css"

const nunito = Nunito({
  variable: "--font-nunito",
  subsets: ["latin"],
  weight: ["400", "600", "700"],
})

export const metadata: Metadata = {
  title: siteConfig.title,
  description: siteConfig.description,
  applicationName: siteConfig.name,
  appleWebApp: {
    capable: true,
    title: siteConfig.name,
    statusBarStyle: "default",
  },
}

// the status bar blends into the page, which reads more like an installed app
export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f5f4fb" },
    { media: "(prefers-color-scheme: dark)", color: "#0d0c1a" },
  ],
  colorScheme: "light dark",
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    // next-themes sets the theme class on <html> before hydration
    <html lang="en" className={nunito.variable} suppressHydrationWarning>
      <body className="flex min-h-full flex-col">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          {children}
        </ThemeProvider>
        <Analytics />
      </body>
    </html>
  )
}
