import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    testTimeout: 10000,
    hookTimeout: 10000,
    teardownTimeout: 5000,
    isolate: true,
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
        minThreads: 1,
        maxThreads: 4,
      },
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov', 'text-summary', 'cobertura', 'json-summary'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/coverage/**',
        '**/dist/**',
        '**/.{idea,git,cache,output,temp}/**',
        '**/{karma,rollup,webpack,vite,vitest,jest,ava,babel,nyc,cypress,tsup,build}.config.*',
        // Exclude specific files that don't need coverage
        'src/main.tsx',
        'src/vite-env.d.ts',
        'src/test/**/*',
        '**/*.stories.*',
        '**/*.test.*',
        '**/*.spec.*',
        '**/mock*',
        '**/__mocks__/**',
        '**/__tests__/**',
        // Exclude demo and example files
        '**/*Demo.tsx',
        '**/*Example.tsx',
        // Exclude type-only files
        'src/types/index.ts',
      ],
      include: [
        'src/**/*.{ts,tsx}',
        '!src/test/**',
        '!src/**/*.test.*',
        '!src/**/*.spec.*',
        '!src/**/*Demo.tsx',
        '!src/**/*Example.tsx',
      ],
      thresholds: {
        global: {
          branches: 75,
          functions: 80,
          lines: 80,
          statements: 80,
        },
        // Per-file thresholds for critical components - adjusted to be more realistic
        'src/components/**/*.{ts,tsx}': {
          branches: 70,
          functions: 75,
          lines: 75,
          statements: 75,
        },
        'src/services/**/*.{ts,tsx}': {
          branches: 80,
          functions: 85,
          lines: 85,
          statements: 85,
        },
        'src/utils/**/*.{ts,tsx}': {
          branches: 85,
          functions: 90,
          lines: 90,
          statements: 90,
        },
        'src/hooks/**/*.{ts,tsx}': {
          branches: 80,
          functions: 85,
          lines: 85,
          statements: 85,
        },
        'src/types/**/*.{ts,tsx}': {
          branches: 95,
          functions: 95,
          lines: 95,
          statements: 95,
        },
      },
      all: true,
      skipFull: false,
      // Enable branch coverage
      reportOnFailure: true,
      // Watermarks for coverage visualization
      watermarks: {
        statements: [80, 95],
        functions: [80, 95],
        branches: [75, 90],
        lines: [80, 95],
      },
    },
    reporters: ['verbose', 'json'],
    outputFile: {
      json: './test-results.json',
    },
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
});