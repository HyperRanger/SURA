# SURA brand assets

All logos are vector SVG with the wordmark already converted to outlines, so no font is needed anywhere.

## Which file to use

| File | Use it for |
|---|---|
| sura-logo.svg | Stacked logo on light backgrounds (docs, deck, splash screen) |
| sura-logo-dark.svg | Stacked logo on indigo or other dark backgrounds |
| sura-logo-horizontal.svg | Website header on light backgrounds |
| sura-logo-horizontal-dark.svg | Website header on dark backgrounds |
| sura-mark.svg | Symbol only, light backgrounds |
| sura-mark-dark.svg | Symbol only, dark backgrounds |
| sura-mark-mono.svg | Single colour indigo, for print or anywhere gold will not show |
| sura-loader.svg | Animated loading indicator |
| favicon.svg, favicon.ico | Browser tab icon |
| apple-touch-icon.png | iPhone home screen icon (180x180) |
| icon-192.png, icon-512.png | Web app manifest icons |
| og-image.png | Link preview when the demo URL is shared (1200x630) |

## Add to the head of index.html

```html
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:image" content="https://YOUR-DEMO-URL/og-image.png">
<meta property="og:title" content="SURA">
<meta property="og:description" content="The infrastructure of commitment.">
<meta name="theme-color" content="#29235C">
```

In a Vite project, put the favicon, icon and og files inside the `public` folder so they are served from the site root.

## Web app manifest icons

```json
{
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

## Loader

Use it as a normal image. The animation runs on its own and stops for users who have reduced motion turned on.

```html
<img src="/sura-loader.svg" width="96" height="96" alt="Loading">
```

## Colours

Deep Indigo #29235C, Sura Gold #D9A441, Soft Ivory #F7F5EF, Near Black #171717.

## Note

These were traced from the PNG you supplied, so edges are clean but very slightly softened on sharp corners. If you have a larger original export, send it and the files can be regenerated at higher fidelity.
