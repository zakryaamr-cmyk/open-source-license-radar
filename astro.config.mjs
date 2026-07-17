import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import rss from '@astrojs/rss';

export default defineConfig({
  site: 'https://license-radar.example.com',
  output: 'static',
  integrations: [
    sitemap({
      filter: (page) => !page.includes('/draft'),
      changefreq: 'daily',
      priority: 0.7,
      lastmod: new Date()
    }),
    rss({
      title: 'Open-Source License Fallback Radar',
      description: 'Track license changes and discover free open-source alternatives',
      xmlns: {
        media: 'http://search.yahoo.com/mrss/'
      }
    })
  ],
  compressHTML: true,
  build: {
    inlineStylesheets: 'auto',
    assets: '_astro'
  },
  prefetch: true
});