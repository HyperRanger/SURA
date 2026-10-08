import type { MetadataRoute } from "next"
import { siteConfig } from "@/config/site"

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: siteConfig.name,
    short_name: siteConfig.name,
    description: siteConfig.description,
    id: "/",
    scope: "/",
    start_url: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#f5f4fb",
    theme_color: "#4c3fd6",
    icons: [
      // `app/icon.png` is emitted by Next.js at this stable route. Keeping the
      // manifest on the emitted asset avoids referring to duplicate public
      // files that may not be present in a deployment.
      { src: "/icon.png", sizes: "512x512", type: "image/png" },
    ],
  }
}
