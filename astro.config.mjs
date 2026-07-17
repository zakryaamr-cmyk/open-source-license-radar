import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://license-radar.example.com',
  output: 'static',
  integrations: [
    sitemap({
      filter: (page) => !page.includes('/draft'),
      changefreq: 'daily',
      priority: 0.7,
      lastmod: new Date()
    })
  ],
  compressHTML: true,
  build: {
    inlineStylesheets: 'auto',
    assets: '_astro'
  },
  prefetch: true
});
