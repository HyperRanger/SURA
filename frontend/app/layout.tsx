import type { Metadata, Viewport } from "next";
import { Nunito } from "next/font/google";
import { siteConfig } from "@/config/site";
import "./globals.css";

const nunito = Nunito({
  variable: "--font-nunito",
  subsets: ["latin"],
  weight: ["400", "600", "700", "800", "900"],
});

export const metadata: Metadata = {
  title: siteConfig.title,
  description: siteConfig.description,
};

export const viewport: Viewport = {
  themeColor: "#29235c",
  colorScheme: "light",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={nunito.variable}>
      <body className="flex min-h-full flex-col">
        {children}
      </body>
    </html>
  );
}
