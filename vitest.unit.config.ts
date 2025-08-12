import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    include: [
      '**/*.test.{ts,tsx}',
      '!**/*.integration.test.{ts,tsx}',
      '!**/*.e2e.test.{ts,tsx}',
    ],
    exclude: [
      'node_modules/',
      'dist/',
      'coverage/',
      '**/*.integration.test.*',
      '**/*.e2e.test.*',
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage/unit',
      include: [
        'src/**/*.{ts,tsx}',
        '!src/test/**',
        '!src/**/*.test.*',
        '!src/**/*.spec.*',
      ],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/coverage/**',
        '**/dist/**',
        'src/main.tsx',
        'src/vite-env.d.ts',
        '**/*.stories.*',
        '**/*.test.*',
        '**/*.spec.*',
        '**/mock*',
        '**/__mocks__/**',
        '**/__tests__/**',
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 85,
          lines: 85,
          statements: 85,
        },
      },
    },
    reporters: ['verbose', 'json'],
    outputFile: {
      json: './test-results-unit.json',
    },
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
});