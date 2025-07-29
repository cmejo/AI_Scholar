import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    include: ['**/*.integration.test.{ts,tsx}'],
    testTimeout: 30000, // Longer timeout for integration tests
    hookTimeout: 30000,
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
});