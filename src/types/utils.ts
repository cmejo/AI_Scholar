// Utility types for better TypeScript experience

// Make all properties optional recursively
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

// Make all properties required recursively
export type DeepRequired<T> = {
  [P in keyof T]-?: T[P] extends object ? DeepRequired<T[P]> : T[P];
};

// Extract function parameters
export type Parameters<T extends (...args: any) => any> = T extends (...args: infer P) => any ? P : never;

// Extract function return type
export type ReturnType<T extends (...args: any) => any> = T extends (...args: any) => infer R ? R : any;

// Make specific properties optional
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

// Make specific properties required
export type RequiredBy<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Create a type with only specific properties
export type PickByType<T, U> = {
  [K in keyof T as T[K] extends U ? K : never]: T[K];
};

// Exclude properties by type
export type OmitByType<T, U> = {
  [K in keyof T as T[K] extends U ? never : K]: T[K];
};

// Create union of all property names
export type KeysOfType<T, U> = {
  [K in keyof T]: T[K] extends U ? K : never;
}[keyof T];

// Create a type that represents a function with specific parameters
export type FunctionWithParams<P extends readonly unknown[], R = void> = (...args: P) => R;

// Create a type for async functions
export type AsyncFunction<T extends (...args: any) => any> = T extends (...args: infer P) => infer R
  ? (...args: P) => Promise<R>
  : never;

// Create a type for event handlers
export type EventHandler<T = Event> = (event: T) => void;

// Create a type for React component props
export type ComponentProps<T> = T extends React.ComponentType<infer P> ? P : never;

// Create a type for React ref
export type RefType<T> = React.RefObject<T> | React.MutableRefObject<T> | ((instance: T | null) => void) | null;

// Create a type for style objects
export type StyleObject = React.CSSProperties;

// Create a type for class names
export type ClassName = string | undefined | null | false | { [key: string]: boolean };

// Create a type for children prop
export type Children = React.ReactNode;

// Create a type for component with children
export type WithChildren<T = {}> = T & { children?: Children };

// Create a type for component with optional children
export type MaybeWithChildren<T = {}> = T & { children?: Children };

// Create a type for HTML element props
export type HTMLElementProps<T extends keyof JSX.IntrinsicElements> = JSX.IntrinsicElements[T];

// Create a type for form elements
export type FormElementProps<T extends HTMLElement> = React.DetailedHTMLProps<React.HTMLAttributes<T>, T>;

// Create a type for input elements
export type InputProps = React.DetailedHTMLProps<React.InputHTMLAttributes<HTMLInputElement>, HTMLInputElement>;

// Create a type for button elements
export type ButtonProps = React.DetailedHTMLProps<React.ButtonHTMLAttributes<HTMLButtonElement>, HTMLButtonElement>;

// Create a type for div elements
export type DivProps = React.DetailedHTMLProps<React.HTMLAttributes<HTMLDivElement>, HTMLDivElement>;

// Create a type for API responses
export type ApiResponse<T = any> = {
  data?: T;
  error?: string;
  message?: string;
  status: number;
  success: boolean;
};

// Create a type for async API calls
export type AsyncApiCall<T = any> = Promise<ApiResponse<T>>;

// Create a type for loading states
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

// Create a type for form validation
export type ValidationResult = {
  isValid: boolean;
  errors: string[];
  warnings?: string[];
};

// Create a type for form field
export type FormField<T = any> = {
  value: T;
  error?: string;
  touched: boolean;
  dirty: boolean;
};

// Create a type for form state
export type FormState<T extends Record<string, any>> = {
  [K in keyof T]: FormField<T[K]>;
};

// Create a type for theme colors
export type ThemeColor = 
  | 'primary' 
  | 'secondary' 
  | 'success' 
  | 'warning' 
  | 'error' 
  | 'info' 
  | 'light' 
  | 'dark';

// Create a type for sizes
export type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

// Create a type for positions
export type Position = 'top' | 'right' | 'bottom' | 'left' | 'center';

// Create a type for alignment
export type Alignment = 'start' | 'center' | 'end' | 'stretch';

// Create a type for breakpoints
export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';

// Create a type for device types
export type DeviceType = 'mobile' | 'tablet' | 'desktop';

// Create a type for orientation
export type Orientation = 'portrait' | 'landscape';

// Create a type for accessibility roles
export type AriaRole = 
  | 'button' 
  | 'link' 
  | 'menuitem' 
  | 'tab' 
  | 'tabpanel' 
  | 'dialog' 
  | 'alert' 
  | 'status' 
  | 'progressbar'
  | 'slider'
  | 'spinbutton'
  | 'textbox'
  | 'combobox'
  | 'listbox'
  | 'option'
  | 'checkbox'
  | 'radio'
  | 'switch'
  | 'toolbar'
  | 'tooltip'
  | 'navigation'
  | 'main'
  | 'banner'
  | 'contentinfo'
  | 'complementary'
  | 'region';

// Create a type for keyboard keys
export type KeyboardKey = 
  | 'Enter' 
  | 'Escape' 
  | 'Space' 
  | 'Tab' 
  | 'ArrowUp' 
  | 'ArrowDown' 
  | 'ArrowLeft' 
  | 'ArrowRight'
  | 'Home'
  | 'End'
  | 'PageUp'
  | 'PageDown'
  | 'Delete'
  | 'Backspace';

// Create a type for mouse buttons
export type MouseButton = 'left' | 'middle' | 'right';

// Create a type for touch gestures
export type TouchGesture = 'tap' | 'swipe' | 'pinch' | 'rotate';

// Create a type for animation states
export type AnimationState = 'idle' | 'running' | 'paused' | 'finished';

// Create a type for transition timing functions
export type TimingFunction = 'ease' | 'ease-in' | 'ease-out' | 'ease-in-out' | 'linear';

// Create a type for performance metrics
export type PerformanceMetric = {
  name: string;
  value: number;
  unit: string;
  timestamp: number;
};

// Create a type for error boundaries
export type ErrorBoundaryState = {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
};

// Create a type for lazy loading states
export type LazyLoadingState = 'idle' | 'loading' | 'loaded' | 'error';

// Utility functions for type checking
export const isString = (value: unknown): value is string => typeof value === 'string';
export const isNumber = (value: unknown): value is number => typeof value === 'number' && !isNaN(value);
export const isBoolean = (value: unknown): value is boolean => typeof value === 'boolean';
export const isObject = (value: unknown): value is object => typeof value === 'object' && value !== null;
export const isArray = (value: unknown): value is unknown[] => Array.isArray(value);
export const isFunction = (value: unknown): value is Function => typeof value === 'function';
export const isUndefined = (value: unknown): value is undefined => typeof value === 'undefined';
export const isNull = (value: unknown): value is null => value === null;
export const isNullOrUndefined = (value: unknown): value is null | undefined => value == null;

// Type guards for React elements
export const isReactElement = (value: unknown): value is React.ReactElement => 
  React.isValidElement(value);

export const isReactComponent = (value: unknown): value is React.ComponentType => 
  isFunction(value) && value.prototype?.isReactComponent;

// Type assertion helpers
export const assertIsString = (value: unknown): asserts value is string => {
  if (!isString(value)) {
    throw new Error(`Expected string, got ${typeof value}`);
  }
};

export const assertIsNumber = (value: unknown): asserts value is number => {
  if (!isNumber(value)) {
    throw new Error(`Expected number, got ${typeof value}`);
  }
};

export const assertIsObject = (value: unknown): asserts value is object => {
  if (!isObject(value)) {
    throw new Error(`Expected object, got ${typeof value}`);
  }
};

// Create a type for environment variables
export type Environment = 'development' | 'production' | 'test';

// Create a type for log levels
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

// Create a type for HTTP methods
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';

// Create a type for HTTP status codes
export type HttpStatusCode = 200 | 201 | 204 | 400 | 401 | 403 | 404 | 409 | 422 | 500 | 502 | 503;

// Create a type for content types
export type ContentType = 
  | 'application/json' 
  | 'application/xml' 
  | 'text/html' 
  | 'text/plain' 
  | 'multipart/form-data'
  | 'application/x-www-form-urlencoded';

// Export all types for easy importing
export type * from './auth';
export type * from './chat';
export type * from './document';
export type * from './integration';
export type * from './workflow';
export type * from './security';