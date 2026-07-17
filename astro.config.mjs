import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  site: 'https://zakryaamr-cmyk.github.io',
  base: '/open-source-license-radar',
  output: 'static',
  integrations: [tailwind()]
});