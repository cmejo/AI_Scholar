/**
 * Type declarations for visualization libraries
 */

// Plotly.js types
declare global {
  interface Window {
    Plotly: {
      newPlot: (div: HTMLElement, data: any[], layout: any, config?: any) => Promise<void>;
      restyle: (div: HTMLElement | string, update: any, traces?: number[]) => Promise<void>;
      relayout: (div: HTMLElement | string, update: any) => Promise<void>;
      react: (div: HTMLElement, data: any[], layout: any, config?: any) => Promise<void>;
      redraw: (div: HTMLElement) => Promise<void>;
      purge: (div: HTMLElement) => void;
    };
    
    // D3.js types
    d3: {
      select: (selector: string | HTMLElement) => any;
      selectAll: (selector: string) => any;
      forceSimulation: (nodes?: any[]) => any;
      forceLink: (links?: any[]) => any;
      forceManyBody: () => any;
      forceCenter: (x: number, y: number) => any;
      drag: () => any;
      schemeCategory10: string[];
      scaleOrdinal: (range?: string[]) => any;
      zoom: () => any;
      event: any;
    };
    
    // Chart.js types
    Chart: {
      new (ctx: CanvasRenderingContext2D, config: any): {
        data: any;
        update: (mode?: string) => void;
        destroy: () => void;
        resize: () => void;
        render: () => void;
        getElementsAtEventForMode: (event: Event, mode: string, options: any, useFinalPosition?: boolean) => any[];
      };
      register: (...items: any[]) => void;
      defaults: any;
    };
    
    // Custom visualization updates
    visualizationUpdates: {
      [key: string]: (updateData: any) => void;
    };
  }
}

// Export empty object to make this a module
export {};