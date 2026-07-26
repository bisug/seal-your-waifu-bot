import type { RsbuildConfig } from '@rsbuild/core';
import { defineConfig, loadEnv } from '@rsbuild/core';
import { pluginReact } from '@rsbuild/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Load .env files with the VITE_ prefix so existing import.meta.env.VITE_* vars
// keep working after the Vite -> Rsbuild migration. Rsbuild has no `source.envPrefix`
// option; instead we load env vars ourselves and inject them via `source.define`.
const { publicVars } = loadEnv({ prefixes: ['VITE_'] });

const isProd = process.env.NODE_ENV === 'production';

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
    // Inject the main script early so the bundle starts downloading before
    // the parser reaches the <script> tag at the bottom of <body>.
    inject: 'head',
    scriptLoading: 'defer',
  },
  output: {
    distPath: { root: 'dist' },
    assetPrefix: '/',
    // Long-term immutable asset caching: filename keyed by content hash.
    filename: {
      js: '[name].[contenthash:8].js',
      css: '[name].[contenthash:8].css',
      svg: '[name].[contenthash:8].svg',
    },
    // Emit asset manifest so the backend / CDN can pre-warm lazy chunks.
    manifest: isProd,
    // Keep source maps in dev, drop them in prod for smaller/faster builds.
    sourceMap: { js: isProd ? false : 'cheap-module-source-map' },
    // Strip React DevTools / test helpers from prod bundles.
    minify: isProd,
    polyfill: 'off',
  },
  performance: {
    // Split vendor chunks to mirror the previous Vite manualChunks config.
    // Rsbuild's chunkSplit with strategy 'custom' delegates to Rspack's
    // optimization.splitChunks.
    chunkSplit: {
      strategy: 'custom',
      splitChunks: {
        // Only split chunks above this size; tiny chunks hurt HTTP/2 parallelism
        // and add round-trips on slow Telegram WebView connections.
        minSize: 20000,
        cacheGroups: {
          react: {
            name: 'react-vendor',
            test: /[\\/]node_modules[\\/](react|react-dom|scheduler)[\\/]/,
            chunks: 'all',
            priority: 10,
          },
          motion: {
            name: 'motion-vendor',
            test: /[\\/]node_modules[\\/]framer-motion[\\/]/,
            chunks: 'all',
            priority: 8,
          },
          query: {
            name: 'query-vendor',
            test: /[\\/]node_modules[\\/]@tanstack[\\/]react-query[\\/]/,
            chunks: 'all',
            priority: 8,
          },
          icons: {
            name: 'icons-vendor',
            test: /[\\/]node_modules[\\/]lucide-react[\\/]/,
            chunks: 'all',
            priority: 8,
          },
        },
      },
    },
    // Pre-fetch lazy chunks so route switches feel instant on slow links.
  },
  tools: {
    rspack: (config, { isProd }) => {
      // Modern Telegram WebView targets are evergreen; ship only ES2015+ syntax
      // so Rspack skips transpiling async/await, optional chaining, etc.
      if (isProd) {
        config.target = ['web', 'es2015'];
      }
      config.output = {
        ...(config.output ?? {}),
        chunkLoadingGlobal: 'webpackChunkSeal',
      };
      return config;
    },
  },
} as RsbuildConfig);

