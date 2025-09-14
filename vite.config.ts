import react from '@vitejs/plugin-react';
import { resolve } from 'path';
import { visualizer } from 'rollup-plugin-visualizer';
import { defineConfig, loadEnv } from 'vite';

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const isProduction = mode === 'production';
  const isDevelopment = mode === 'development';
  
  return {
    plugins: [
      react({
        fastRefresh: isDevelopment,
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
      include: [
        'react',
        'react-dom',
        'react/jsx-runtime',
        'lucide-react',
      ],
      exclude: [],
      // Force optimization of specific dependencies
      force: isProduction,
    },

    // Enhanced build optimizations
    build: {
      target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari13.1'],
      sourcemap: isDevelopment,
      minify: isProduction ? 'terser' : false,
      cssCodeSplit: true,
      
      // Optimize chunk splitting
      rollupOptions: {
        // Enhanced tree shaking
        treeshake: {
          moduleSideEffects: false,
          propertyReadSideEffects: false,
          unknownGlobalSideEffects: false,
        },
        
        // Input configuration
        input: {
          main: resolve(__dirname, 'index.html'),
        },
        
        output: {
          // Advanced manual chunking strategy
          manualChunks: (id) => {
            // Vendor chunks
            if (id.includes('node_modules')) {
              // React ecosystem
              if (id.includes('react') || id.includes('react-dom')) {
                return 'vendor-react';
              }
              // UI libraries
              if (id.includes('lucide-react')) {
                return 'vendor-icons';
              }
              // Other vendor dependencies
              return 'vendor-libs';
            }
            
            // Feature-based chunks
            if (id.includes('/components/navigation/')) {
              return 'chunk-navigation';
            }
            if (id.includes('/components/monitoring/') || id.includes('/components/accessibility/')) {
              return 'chunk-tools';
            }
            if (id.includes('/components/enterprise/')) {
              return 'chunk-enterprise';
            }
            if (id.includes('/components/')) {
              return 'chunk-components';
            }
            
            // Utilities and hooks
            if (id.includes('/hooks/') || id.includes('/utils/')) {
              return 'chunk-utils';
            }
            
            // Services
            if (id.includes('/services/')) {
              return 'chunk-services';
            }
            
            // Types and contexts
            if (id.includes('/types/') || id.includes('/contexts/')) {
              return 'chunk-shared';
            }
          },
          
          // Optimize chunk file names
          chunkFileNames: (chunkInfo) => {
            const facadeModuleId = chunkInfo.facadeModuleId
              ? chunkInfo.facadeModuleId.split('/').pop()?.replace('.tsx', '').replace('.ts', '')
              : 'chunk';
            return `js/[name]-[hash].js`;
          },
          
          // Optimize entry file names
          entryFileNames: 'js/[name]-[hash].js',
          
          // Optimize asset file names
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name?.split('.') || [];
            const ext = info[info.length - 1];
            if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext || '')) {
              return `assets/images/[name]-[hash][extname]`;
            }
            if (/css/i.test(ext || '')) {
              return `assets/css/[name]-[hash][extname]`;
            }
            if (/woff2?|eot|ttf|otf/i.test(ext || '')) {
              return `assets/fonts/[name]-[hash][extname]`;
            }
            return `assets/[name]-[hash][extname]`;
          },
          
          // Optimize chunk size warnings
          experimentalMinChunkSize: 15000, // 15KB minimum chunk size
        },
        
        // External dependencies (don't bundle these)
        external: (id) => {
          // Keep all dependencies bundled for better performance
          return false;
        },
      },
    
      // Enhanced Terser options for production
      terserOptions: isProduction ? {
        compress: {
          drop_console: true,
          drop_debugger: true,
          pure_funcs: ['console.log', 'console.info', 'console.debug', 'console.warn'],
          passes: 2,
        },
        mangle: {
          safari10: true,
          properties: {
            regex: /^_/,
          },
        },
        format: {
          comments: false,
        },
      } : undefined,
    
      // Chunk size warnings
      chunkSizeWarningLimit: 1000, // Increased to 1MB for better chunking
      
      // CSS optimization
      cssMinify: isProduction,
    },

  // Development server optimizations
  server: {
    host: '0.0.0.0', // Bind to all interfaces
    port: 3000,
    strictPort: false, // Allow fallback ports
    hmr: {
      overlay: true,
    },
  },

    // Path resolution with aliases
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
        '@/components': resolve(__dirname, 'src/components'),
        '@/hooks': resolve(__dirname, 'src/hooks'),
        '@/utils': resolve(__dirname, 'src/utils'),
        '@/services': resolve(__dirname, 'src/services'),
        '@/types': resolve(__dirname, 'src/types'),
        '@/contexts': resolve(__dirname, 'src/contexts'),
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
