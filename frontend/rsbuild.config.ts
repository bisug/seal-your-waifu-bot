import { defineConfig, loadEnv } from '@rsbuild/core';
import { pluginReact } from '@rsbuild/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Load .env files with the VITE_ prefix so existing import.meta.env.VITE_* vars
// keep working after the Vite -> Rsbuild migration. Rsbuild has no `source.envPrefix`
// option; instead we load env vars ourselves and inject them via `source.define`.
const { publicVars } = loadEnv({ prefixes: ['VITE_'] });

export default defineConfig({
  plugins: [pluginReact()],
  source: {
    entry: { index: './src/main.tsx' },
    // Re-expose VITE_* env vars as import.meta.env.VITE_* (and process.env.VITE_*)
    // so existing source code that reads import.meta.env.VITE_* works unchanged.
    define: publicVars,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  html: {
    template: './index.html',
  },
  output: {
    distPath: { root: 'dist' },
    assetPrefix: '/',
  },
  performance: {
    // Split vendor chunks to mirror the previous Vite manualChunks config.
    // Rsbuild's chunkSplit with strategy 'custom' delegates to Rspack's
    // optimization.splitChunks.
    chunkSplit: {
      strategy: 'custom',
      splitChunks: {
        cacheGroups: {
          'react-vendor': {
            name: 'react-vendor',
            test: /[\\/]node_modules[\\/](react|react-dom|scheduler)[\\/]/,
            chunks: 'all',
            priority: 10,
          },
          'motion-vendor': {
            name: 'motion-vendor',
            test: /[\\/]node_modules[\\/]framer-motion[\\/]/,
            chunks: 'all',
            priority: 8,
          },
          'query-vendor': {
            name: 'query-vendor',
            test: /[\\/]node_modules[\\/]@tanstack[\\/]react-query[\\/]/,
            chunks: 'all',
            priority: 8,
          },
          'icons-vendor': {
            name: 'icons-vendor',
            test: /[\\/]node_modules[\\/]lucide-react[\\/]/,
            chunks: 'all',
            priority: 8,
          },
        },
      },
    },
  },
});
