/**
 * Type declarations for visualization libraries
 */

// Plotly.js types
interface PlotlyData {
  x?: (string | number)[];
  y?: (string | number)[];
  z?: (string | number)[];
  type?: string;
  mode?: string;
  name?: string;
  marker?: {
    color?: string | string[];
    size?: number | number[];
    opacity?: number;
  };
  line?: {
    color?: string;
    width?: number;
  };
  text?: string | string[];
  hovertemplate?: string;
  [key: string]: unknown;
}

interface PlotlyLayout {
  title?: string | { text: string; font?: { size?: number; color?: string } };
  xaxis?: {
    title?: string;
    type?: string;
    range?: [number, number];
    showgrid?: boolean;
  };
  yaxis?: {
    title?: string;
    type?: string;
    range?: [number, number];
    showgrid?: boolean;
  };
  width?: number;
  height?: number;
  margin?: {
    l?: number;
    r?: number;
    t?: number;
    b?: number;
  };
  showlegend?: boolean;
  [key: string]: unknown;
}

interface PlotlyConfig {
  displayModeBar?: boolean;
  responsive?: boolean;
  toImageButtonOptions?: {
    format?: string;
    filename?: string;
    height?: number;
    width?: number;
    scale?: number;
  };
  [key: string]: unknown;
}

// D3.js types
interface D3Selection {
  attr: (name: string, value?: string | number | ((d: unknown, i: number) => string | number)) => D3Selection;
  style: (name: string, value?: string | number | ((d: unknown, i: number) => string | number)) => D3Selection;
  text: (value?: string | ((d: unknown, i: number) => string)) => D3Selection;
  append: (type: string) => D3Selection;
  selectAll: (selector: string) => D3Selection;
  data: (data: unknown[]) => D3Selection;
  enter: () => D3Selection;
  exit: () => D3Selection;
  remove: () => D3Selection;
  on: (type: string, listener: (d: unknown, i: number) => void) => D3Selection;
  call: (func: (selection: D3Selection) => void) => D3Selection;
  [key: string]: unknown;
}

interface D3Force {
  strength: (strength?: number | ((d: unknown, i: number) => number)) => D3Force;
  distance: (distance?: number | ((d: unknown, i: number) => number)) => D3Force;
  id: (id?: (d: unknown, i: number) => string) => D3Force;
  links: (links?: unknown[]) => D3Force;
  [key: string]: unknown;
}

interface D3Simulation {
  nodes: (nodes?: unknown[]) => D3Simulation;
  force: (name: string, force?: D3Force | null) => D3Simulation;
  on: (type: string, listener: () => void) => D3Simulation;
  restart: () => D3Simulation;
  stop: () => D3Simulation;
  alpha: (alpha?: number) => D3Simulation | number;
  alphaTarget: (target?: number) => D3Simulation | number;
  [key: string]: unknown;
}

interface D3Scale {
  domain: (domain?: string[]) => D3Scale;
  range: (range?: string[]) => D3Scale;
  (value: string): string;
  [key: string]: unknown;
}

interface D3Zoom {
  scaleExtent: (extent?: [number, number]) => D3Zoom;
  on: (type: string, listener: () => void) => D3Zoom;
  transform: (selection: D3Selection, transform: unknown) => void;
  [key: string]: unknown;
}

interface D3Drag {
  on: (type: string, listener: (d: unknown) => void) => D3Drag;
  [key: string]: unknown;
}

// Chart.js types
interface ChartData {
  labels?: string[];
  datasets: ChartDataset[];
}

interface ChartDataset {
  label?: string;
  data: (number | { x: number; y: number })[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  fill?: boolean;
  tension?: number;
  [key: string]: unknown;
}

interface ChartOptions {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  scales?: {
    x?: {
      display?: boolean;
      title?: { display?: boolean; text?: string };
    };
    y?: {
      display?: boolean;
      title?: { display?: boolean; text?: string };
    };
  };
  plugins?: {
    legend?: { display?: boolean };
    title?: { display?: boolean; text?: string };
  };
  [key: string]: unknown;
}

interface ChartConfig {
  type: string;
  data: ChartData;
  options?: ChartOptions;
}

interface ChartInstance {
  data: ChartData;
  update: (mode?: string) => void;
  destroy: () => void;
  resize: () => void;
  render: () => void;
  getElementsAtEventForMode: (event: Event, mode: string, options: Record<string, unknown>, useFinalPosition?: boolean) => unknown[];
}

declare global {
  interface Window {
    Plotly: {
      newPlot: (div: HTMLElement, data: PlotlyData[], layout: PlotlyLayout, config?: PlotlyConfig) => Promise<void>;
      restyle: (div: HTMLElement | string, update: Record<string, unknown>, traces?: number[]) => Promise<void>;
      relayout: (div: HTMLElement | string, update: Record<string, unknown>) => Promise<void>;
      react: (div: HTMLElement, data: PlotlyData[], layout: PlotlyLayout, config?: PlotlyConfig) => Promise<void>;
      redraw: (div: HTMLElement) => Promise<void>;
      purge: (div: HTMLElement) => void;
    };
    
    // D3.js types
    d3: {
      select: (selector: string | HTMLElement) => D3Selection;
      selectAll: (selector: string) => D3Selection;
      forceSimulation: (nodes?: unknown[]) => D3Simulation;
      forceLink: (links?: unknown[]) => D3Force;
      forceManyBody: () => D3Force;
      forceCenter: (x: number, y: number) => D3Force;
      drag: () => D3Drag;
      schemeCategory10: string[];
      scaleOrdinal: (range?: string[]) => D3Scale;
      zoom: () => D3Zoom;
      event: Event | null;
    };
    
    // Chart.js types
    Chart: {
      new (ctx: CanvasRenderingContext2D, config: ChartConfig): ChartInstance;
      register: (...items: unknown[]) => void;
      defaults: Record<string, unknown>;
    };
    
    // Custom visualization updates
    visualizationUpdates: Record<string, (updateData: Record<string, unknown>) => void>;
  }
}

// Export empty object to make this a module
export { };
