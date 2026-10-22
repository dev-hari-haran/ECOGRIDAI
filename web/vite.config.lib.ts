import fs from 'node:fs'
import path from 'node:path'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// Library-mode build config used when publishing this Make as a Make Kit
// (npm package). The dev server uses vite.config.ts; this config is only
// invoked via `pnpm run build:lib`. Type declarations are emitted separately
// by `tsc -p tsconfig.types.json` (see the build:lib script in package.json).

// Externalize runtime + peer dependencies so the published package doesn't
// bundle them — consumers provide their own React etc. Mirrors Foundry's
// createPackageConfig external predicate.
function readExternalDeps(): string[] {
  try {
    const pkg = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'package.json'), 'utf-8')) as {
      dependencies?: Record<string, string>
      peerDependencies?: Record<string, string>
    }
    return [...Object.keys(pkg.dependencies ?? {}), ...Object.keys(pkg.peerDependencies ?? {})]
  } catch {
    return ['react', 'react-dom']
  }
}

const externalDeps = readExternalDeps()
function isExternal(id: string): boolean {
  // Externalize each dep and its subpath imports (e.g. react, react/jsx-runtime).
  return externalDeps.some((dep) => id === dep || id.startsWith(dep + '/'))
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  assetsInclude: ['**/*.svg', '**/*.csv'],
  build: {
    lib: {
      entry: ['./src/index.ts'],
      formats: ['es'],
      cssFileName: 'style',
    },
    rollupOptions: {
      external: isExternal,
      output: {
        preserveModules: true,
        preserveModulesRoot: 'src',
        entryFileNames: '[name].js',
      },
    },
  },
})
