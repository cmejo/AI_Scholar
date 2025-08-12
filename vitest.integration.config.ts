import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    include: [
      '**/*.integration.test.{ts,tsx}',
      'src/test/integration.test.ts',
    ],
    exclude: [
      'node_modules/',
      'dist/',
      'coverage/',
      '**/*.test.{ts,tsx}',
      '!**/*.integration.test.{ts,tsx}',
    ],
    testTimeout: 30000, // Longer timeout for integration tests
    hookTimeout: 30000,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './coverage/integration',
      include: [
        'src/**/*.{ts,tsx}',
        '!src/test/**',
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
      ],
    },
    reporters: ['verbose', 'json'],
    outputFile: {
      json: './test-results-integration.json',
    },
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
});