/**
 * Enhanced render utilities for React Testing Library with type safety
 */

import { render, type RenderOptions, type RenderResult } from '@testing-library/react';
import type { ReactElement } from 'react';
import React from 'react';
import { vi } from 'vitest';

/**
 * Interface for test context providers
 */
interface TestProviders {
  ErrorBoundary?: React.ComponentType<{ children: React.ReactNode }>;
  ThemeProvider?: React.ComponentType<{ children: React.ReactNode }>;
  RouterProvider?: React.ComponentType<{ children: React.ReactNode }>;
  QueryProvider?: React.ComponentType<{ children: React.ReactNode }>;
}

/**
 * Interface for render options with providers
 */
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  providers?: TestProviders;
  initialProps?: Record<string, any>;
  mockServices?: Record<string, any>;
}

/**
 * Create a wrapper component with all necessary providers
 */
const createWrapper = (providers: TestProviders = {}) => {
  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    let wrappedChildren = children;

    // Wrap with providers in reverse order (innermost first)
    if (providers.QueryProvider) {
      wrappedChildren = React.createElement(providers.QueryProvider, {}, wrappedChildren);
    }

    if (providers.RouterProvider) {
      wrappedChildren = React.createElement(providers.RouterProvider, {}, wrappedChildren);
    }

    if (providers.ThemeProvider) {
      wrappedChildren = React.createElement(providers.ThemeProvider, {}, wrappedChildren);
    }

    if (providers.ErrorBoundary) {
      wrappedChildren = React.createElement(providers.ErrorBoundary, {}, wrappedChildren);
    }

    return wrappedChildren as ReactElement;
  };

  return Wrapper;
};

/**
 * Enhanced render function with automatic provider setup
 */
export const renderWithProviders = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
): RenderResult => {
  const { providers, initialProps, mockServices, ...renderOptions } = options;

  // Set up mock services if provided
  if (mockServices) {
    Object.entries(mockServices).forEach(([serviceName, mockImplementation]) => {
      vi.doMock(`../../services/${serviceName}`, () => ({
        default: mockImplementation,
      }));
    });
  }

  const Wrapper = createWrapper(providers);

  return render(ui, {
    wrapper: Wrapper,
    ...renderOptions,
  });
};

/**
 * Render component with error boundary for testing error scenarios
 */
export const renderWithErrorBoundary = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
): RenderResult & { errorBoundary: { hasError: boolean; error: Error | null } } => {
  let errorBoundaryState = { hasError: false, error: null as Error | null };

  const TestErrorBoundary: React.ComponentType<{ children: React.ReactNode }> = ({ children }) => {
    const [hasError, setHasError] = React.useState(false);
    const [error, setError] = React.useState<Error | null>(null);

    React.useEffect(() => {
      errorBoundaryState = { hasError, error };
    }, [hasError, error]);

    const componentDidCatch = (error: Error) => {
      setHasError(true);
      setError(error);
    };

    if (hasError) {
      return React.createElement('div', { 'data-testid': 'error-boundary' }, 
        'Something went wrong: ', error?.message
      );
    }

    try {
      return children as ReactElement;
    } catch (error) {
      componentDidCatch(error as Error);
      return React.createElement('div', { 'data-testid': 'error-boundary' }, 
        'Something went wrong: ', (error as Error)?.message
      );
    }
  };

  const result = renderWithProviders(ui, {
    ...options,
    providers: {
      ...options.providers,
      ErrorBoundary: TestErrorBoundary,
    },
  });

  return {
    ...result,
    errorBoundary: errorBoundaryState,
  };
};

/**
 * Render component with mock router for testing navigation
 */
export const renderWithRouter = (
  ui: ReactElement,
  options: CustomRenderOptions & {
    initialRoute?: string;
    routes?: string[];
  } = {}
): RenderResult & { navigate: (path: string) => void } => {
  const { initialRoute = '/', routes = ['/'], ...renderOptions } = options;
  
  let currentRoute = initialRoute;
  const navigate = vi.fn((path: string) => {
    currentRoute = path;
  });

  const MockRouter: React.ComponentType<{ children: React.ReactNode }> = ({ children }) => {
    const [route, setRoute] = React.useState(currentRoute);

    React.useEffect(() => {
      navigate.mockImplementation((path: string) => {
        setRoute(path);
        currentRoute = path;
      });
    }, []);

    // Mock router context
    const routerContext = {
      location: { pathname: route },
      navigate,
      params: {},
      searchParams: new URLSearchParams(),
    };

    return React.createElement(
      'div',
      { 'data-testid': 'mock-router', 'data-current-route': route },
      children
    );
  };

  const result = renderWithProviders(ui, {
    ...renderOptions,
    providers: {
      ...renderOptions.providers,
      RouterProvider: MockRouter,
    },
  });

  return {
    ...result,
    navigate,
  };
};

/**
 * Render component with theme provider for testing different themes
 */
export const renderWithTheme = (
  ui: ReactElement,
  options: CustomRenderOptions & {
    theme?: 'light' | 'dark';
    customTheme?: Record<string, any>;
  } = {}
): RenderResult & { setTheme: (theme: 'light' | 'dark') => void } => {
  const { theme = 'light', customTheme, ...renderOptions } = options;
  
  let currentTheme = theme;
  const setTheme = vi.fn((newTheme: 'light' | 'dark') => {
    currentTheme = newTheme;
  });

  const MockThemeProvider: React.ComponentType<{ children: React.ReactNode }> = ({ children }) => {
    const [activeTheme, setActiveTheme] = React.useState(currentTheme);

    React.useEffect(() => {
      setTheme.mockImplementation((newTheme: 'light' | 'dark') => {
        setActiveTheme(newTheme);
        currentTheme = newTheme;
      });
    }, []);

    const themeValue = customTheme || {
      mode: activeTheme,
      colors: activeTheme === 'light' 
        ? { primary: '#007bff', background: '#ffffff', text: '#000000' }
        : { primary: '#0d6efd', background: '#000000', text: '#ffffff' },
    };

    return React.createElement(
      'div',
      { 
        'data-testid': 'theme-provider', 
        'data-theme': activeTheme,
        style: { 
          backgroundColor: themeValue.colors.background,
          color: themeValue.colors.text,
        }
      },
      children
    );
  };

  const result = renderWithProviders(ui, {
    ...renderOptions,
    providers: {
      ...renderOptions.providers,
      ThemeProvider: MockThemeProvider,
    },
  });

  return {
    ...result,
    setTheme,
  };
};

/**
 * Render component with query provider for testing data fetching
 */
export const renderWithQuery = (
  ui: ReactElement,
  options: CustomRenderOptions & {
    queryData?: Record<string, any>;
    queryErrors?: Record<string, Error>;
  } = {}
): RenderResult & { 
  setQueryData: (key: string, data: any) => void;
  setQueryError: (key: string, error: Error) => void;
} => {
  const { queryData = {}, queryErrors = {}, ...renderOptions } = options;
  
  let currentQueryData = { ...queryData };
  let currentQueryErrors = { ...queryErrors };
  
  const setQueryData = vi.fn((key: string, data: any) => {
    currentQueryData[key] = data;
    delete currentQueryErrors[key];
  });
  
  const setQueryError = vi.fn((key: string, error: Error) => {
    currentQueryErrors[key] = error;
    delete currentQueryData[key];
  });

  const MockQueryProvider: React.ComponentType<{ children: React.ReactNode }> = ({ children }) => {
    const [data, setData] = React.useState(currentQueryData);
    const [errors, setErrors] = React.useState(currentQueryErrors);

    React.useEffect(() => {
      setQueryData.mockImplementation((key: string, newData: any) => {
        setData(prev => ({ ...prev, [key]: newData }));
        setErrors(prev => {
          const newErrors = { ...prev };
          delete newErrors[key];
          return newErrors;
        });
      });

      setQueryError.mockImplementation((key: string, error: Error) => {
        setErrors(prev => ({ ...prev, [key]: error }));
        setData(prev => {
          const newData = { ...prev };
          delete newData[key];
          return newData;
        });
      });
    }, []);

    // Mock query context
    const queryContext = {
      data,
      errors,
      isLoading: false,
      refetch: vi.fn(),
    };

    return React.createElement(
      'div',
      { 'data-testid': 'query-provider' },
      children
    );
  };

  const result = renderWithProviders(ui, {
    ...renderOptions,
    providers: {
      ...renderOptions.providers,
      QueryProvider: MockQueryProvider,
    },
  });

  return {
    ...result,
    setQueryData,
    setQueryError,
  };
};

/**
 * Render component with all providers for comprehensive testing
 */
export const renderWithAllProviders = (
  ui: ReactElement,
  options: CustomRenderOptions & {
    theme?: 'light' | 'dark';
    initialRoute?: string;
    queryData?: Record<string, any>;
  } = {}
): RenderResult & {
  setTheme: (theme: 'light' | 'dark') => void;
  navigate: (path: string) => void;
  setQueryData: (key: string, data: any) => void;
} => {
  const { theme = 'light', initialRoute = '/', queryData = {}, ...renderOptions } = options;
  
  // Combine all provider utilities
  let currentTheme = theme;
  let currentRoute = initialRoute;
  let currentQueryData = { ...queryData };
  
  const setTheme = vi.fn((newTheme: 'light' | 'dark') => {
    currentTheme = newTheme;
  });
  
  const navigate = vi.fn((path: string) => {
    currentRoute = path;
  });
  
  const setQueryData = vi.fn((key: string, data: any) => {
    currentQueryData[key] = data;
  });

  const AllProvidersWrapper: React.ComponentType<{ children: React.ReactNode }> = ({ children }) => {
    return React.createElement(
      'div',
      { 
        'data-testid': 'all-providers-wrapper',
        'data-theme': currentTheme,
        'data-route': currentRoute,
      },
      children
    );
  };

  const result = renderWithProviders(ui, {
    ...renderOptions,
    providers: {
      ...renderOptions.providers,
      ThemeProvider: AllProvidersWrapper,
    },
  });

  return {
    ...result,
    setTheme,
    navigate,
    setQueryData,
  };
};

/**
 * Default render function that can be used as a drop-in replacement
 */
export const customRender = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
): RenderResult => {
  return renderWithProviders(ui, options);
};

// Re-export everything from @testing-library/react
export * from '@testing-library/react';

// Override the default render
export { customRender as render };
