import react from '@vitejs/plugin-react';
import { resolve } from 'path';
import { visualizer } from 'rollup-plugin-visualizer';
import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const isProduction = mode === 'production';
  const isDevelopment = mode === 'development';
  
  return {
    plugins: [
      react({
        fastRefresh: isDevelopment,
        babel: {
          plugins: isProduction ? [
            ['babel-plugin-react-remove-properties', { properties: ['data-testid'] }]
          ] : []
        }
      }),
      // Bundle analyzer plugin
      visualizer({
        filename: 'dist/bundle-analysis.html',
        open: false,
        gzipSize: true,
        brotliSize: true,
        template: 'treemap'
      }),
    ],
  
  // Optimize dependencies
  optimizeDeps: {
    exclude: ['lucide-react'],
    include: [
      'react',
      'react-dom',
      'react/jsx-runtime',
    ],
    // Force optimization of specific dependencies
    force: process.env.NODE_ENV === 'production',
  },

    // Build optimizations
    build: {
      target: 'esnext',
      sourcemap: isDevelopment,
      minify: isProduction ? 'terser' : false,
    
    // Optimize chunk splitting
    rollupOptions: {
      // Enhanced tree shaking
      treeshake: {
        moduleSideEffects: false,
        propertyReadSideEffects: false,
        unknownGlobalSideEffects: false,
      },
      
      output: {
        // Advanced manual chunking strategy
        manualChunks: (id) => {
          // Vendor chunk for React and core libraries
          if (id.includes('node_modules')) {
            if (id.includes('react') || id.includes('react-dom')) {
              return 'vendor-react';
            }
            if (id.includes('lucide-react')) {
              return 'vendor-icons';
            }
            // Other vendor dependencies
            return 'vendor-libs';
          }
          
          // Component chunks
          if (id.includes('/components/')) {
            return 'components';
          }
          
          // Utilities chunk
          if (id.includes('/utils/') || id.includes('/hooks/')) {
            return 'utils';
          }
          
          // Services chunk
          if (id.includes('/services/')) {
            return 'services';
          }
        },
        
        // Optimize chunk file names
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId
            ? chunkInfo.facadeModuleId.split('/').pop()?.replace('.tsx', '').replace('.ts', '')
            : 'chunk';
          return `js/${facadeModuleId}-[hash].js`;
        },
        
        // Optimize asset file names
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') || [];
          const ext = info[info.length - 1];
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext || '')) {
            return `img/[name]-[hash][extname]`;
          }
          if (/css/i.test(ext || '')) {
            return `css/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        },
        
        // Optimize chunk size warnings
        experimentalMinChunkSize: 20000, // 20KB minimum chunk size
      },
      
      // External dependencies (don't bundle these)
      external: (id) => {
        // Keep all dependencies bundled for now
        return false;
      },
    },
    
      // Terser options for production
      terserOptions: isProduction ? {
        compress: {
          drop_console: true,
          drop_debugger: true,
          pure_funcs: ['console.log', 'console.info', 'console.debug']
        },
        mangle: {
          safari10: true
        },
        format: {
          comments: false
        }
      } : undefined,
    
    // Chunk size warnings
    chunkSizeWarningLimit: 500,
    
    // Target modern browsers for better optimization
    target: 'esnext',
  },

  // Development server optimizations
  server: {
    hmr: {
      overlay: true,
    },
  },

  // Path resolution
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@hooks': resolve(__dirname, 'src/hooks'),
      '@services': resolve(__dirname, 'src/services'),
      '@types': resolve(__dirname, 'src/types'),
    },
  },

    // Performance optimizations
    esbuild: {
      // Remove console logs in production
      drop: isProduction ? ['console', 'debugger'] : [],
    },
    
    // Environment variables
    define: {
      __APP_VERSION__: JSON.stringify(env.npm_package_version || '2.0.0'),
      __BUILD_TIME__: JSON.stringify(new Date().toISOString())
    }
  };
});
