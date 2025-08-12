/**
 * @fileoverview Chart Service for rendering interactive analytics charts
 * Provides comprehensive charting capabilities using HTML5 Canvas for data visualization.
 * Supports multiple chart types including line, bar, pie, doughnut, and area charts.
 * 
 * @author AI Scholar Team
 * @version 1.0.0
 * @since 2024-01-01
 */

import { ChartInstance, ChartStats } from '../types/api';

/**
 * Represents a single data point in a chart
 * @interface ChartDataPoint
 */
export interface ChartDataPoint {
  /** X-axis value (numeric or string) */
  x: number | string;
  /** Y-axis value (numeric) */
  y: number;
  /** Optional label for the data point */
  label?: string;
}

/**
 * Represents a dataset for chart rendering
 * @interface ChartDataset
 */
export interface ChartDataset {
  /** Display label for the dataset */
  label: string;
  /** Array of data values or data points */
  data: number[] | ChartDataPoint[];
  /** Background color(s) for the dataset */
  backgroundColor?: string | string[];
  /** Border color for the dataset */
  borderColor?: string;
  /** Border width in pixels */
  borderWidth?: number;
  /** Whether to fill the area under the line (for line/area charts) */
  fill?: boolean;
}

/**
 * Complete configuration object for chart rendering
 * @interface ChartConfiguration
 */
export interface ChartConfiguration {
  /** Type of chart to render */
  type: 'line' | 'bar' | 'pie' | 'doughnut' | 'area' | 'scatter';
  /** Chart data including labels and datasets */
  data: {
    /** Labels for the x-axis or legend */
    labels: string[];
    /** Array of datasets to render */
    datasets: ChartDataset[];
  };
  /** Optional chart configuration options */
  options?: {
    /** Whether the chart should be responsive */
    responsive?: boolean;
    /** Whether to maintain aspect ratio when resizing */
    maintainAspectRatio?: boolean;
    /** Whether to animate chart rendering */
    animation?: boolean;
    /** Legend configuration */
    legend?: {
      /** Whether to display the legend */
      display: boolean;
      /** Position of the legend */
      position: 'top' | 'bottom' | 'left' | 'right';
    };
    /** Tooltip configuration */
    tooltip?: {
      /** Whether tooltips are enabled */
      enabled: boolean;
      /** Background color of tooltips */
      backgroundColor?: string;
      /** Title text color */
      titleColor?: string;
      /** Body text color */
      bodyColor?: string;
    };
    /** Axis scaling configuration */
    scales?: {
      /** X-axis configuration */
      x?: {
        /** Whether to display the x-axis */
        display: boolean;
        /** Grid line configuration */
        grid?: { display: boolean; color?: string };
        /** Tick mark configuration */
        ticks?: { color?: string };
      };
      /** Y-axis configuration */
      y?: {
        /** Whether to display the y-axis */
        display: boolean;
        /** Grid line configuration */
        grid?: { display: boolean; color?: string };
        /** Tick mark configuration */
        ticks?: { color?: string };
      };
    };
  };
}

/**
 * Chart Service for rendering interactive analytics charts
 * 
 * Provides comprehensive charting capabilities using HTML5 Canvas API.
 * Implements singleton pattern to manage chart instances efficiently.
 * Supports multiple chart types with customizable styling and animations.
 * 
 * @class ChartService
 * @example
 * ```typescript
 * import { chartService } from './chartService';
 * 
 * // Render a line chart
 * chartService.renderChart('myChart', {
 *   type: 'line',
 *   data: {
 *     labels: ['Jan', 'Feb', 'Mar'],
 *     datasets: [{
 *       label: 'Sales',
 *       data: [100, 150, 200],
 *       borderColor: '#3B82F6'
 *     }]
 *   }
 * });
 * 
 * // Export chart as image
 * const imageData = chartService.exportChart('myChart', 'png');
 * ```
 */
export class ChartService {
  /** Singleton instance */
  private static instance: ChartService;
  /** Map of active chart instances */
  private chartInstances: Map<string, ChartInstance> = new Map();

  /**
   * Get singleton instance of ChartService
   * 
   * @returns {ChartService} The singleton ChartService instance
   * @static
   */
  static getInstance(): ChartService {
    if (!ChartService.instance) {
      ChartService.instance = new ChartService();
    }
    return ChartService.instance;
  }

  /**
   * Render a chart on a canvas element
   */
  renderChart(
    canvasId: string,
    config: ChartConfiguration,
    width: number = 400,
    height: number = 300
  ): void {
    const canvas = document.getElementById(canvasId) as HTMLCanvasElement;
    if (!canvas) {
      console.error(`Canvas element with id ${canvasId} not found`);
      return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      console.error('Could not get 2D context from canvas');
      return;
    }

    // Set canvas dimensions
    canvas.width = width;
    canvas.height = height;

    // Clear previous chart
    this.destroyChart(canvasId);

    // Render based on chart type
    switch (config.type) {
      case 'line':
        this.renderLineChart(ctx, config, width, height);
        break;
      case 'bar':
        this.renderBarChart(ctx, config, width, height);
        break;
      case 'pie':
        this.renderPieChart(ctx, config, width, height);
        break;
      case 'doughnut':
        this.renderDoughnutChart(ctx, config, width, height);
        break;
      case 'area':
        this.renderAreaChart(ctx, config, width, height);
        break;
      default:
        console.warn(`Chart type ${config.type} not implemented`);
    }

    // Store chart instance for later cleanup
    this.chartInstances.set(canvasId, { config, canvas });
  }

  /**
   * Destroy a chart instance
   */
  destroyChart(canvasId: string): void {
    const instance = this.chartInstances.get(canvasId);
    if (instance) {
      const ctx = instance.canvas.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, instance.canvas.width, instance.canvas.height);
      }
      this.chartInstances.delete(canvasId);
    }
  }

  /**
   * Update chart data
   */
  updateChart(canvasId: string, newData: ChartConfiguration['data']): void {
    const instance = this.chartInstances.get(canvasId);
    if (instance) {
      const updatedConfig = { ...instance.config, data: newData };
      this.renderChart(
        canvasId,
        updatedConfig,
        instance.canvas.width,
        instance.canvas.height
      );
    }
  }

  /**
   * Render line chart
   */
  private renderLineChart(
    ctx: CanvasRenderingContext2D,
    config: ChartConfiguration,
    width: number,
    height: number
  ): void {
    const padding = 40;
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Set styles
    ctx.fillStyle = '#374151'; // Gray background
    ctx.fillRect(0, 0, width, height);

    const dataset = config.data.datasets[0];
    const values = dataset.data as number[];
    const labels = config.data.labels;

    if (values.length === 0) return;

    const max = Math.max(...values);
    const min = Math.min(...values);
    const range = max - min || 1;

    // Draw grid lines
    ctx.strokeStyle = '#4B5563';
    ctx.lineWidth = 1;
    
    // Horizontal grid lines
    for (let i = 0; i <= 5; i++) {
      const y = padding + (i / 5) * chartHeight;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
    }

    // Vertical grid lines
    for (let i = 0; i < labels.length; i++) {
      const x = padding + (i / (labels.length - 1)) * chartWidth;
      ctx.beginPath();
      ctx.moveTo(x, padding);
      ctx.lineTo(x, height - padding);
      ctx.stroke();
    }

    // Draw line
    ctx.strokeStyle = dataset.borderColor || '#3B82F6';
    ctx.lineWidth = dataset.borderWidth || 2;
    ctx.beginPath();

    values.forEach((value, index) => {
      const x = padding + (index / (values.length - 1)) * chartWidth;
      const y = height - padding - ((value - min) / range) * chartHeight;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Draw points
    ctx.fillStyle = dataset.borderColor || '#3B82F6';
    values.forEach((value, index) => {
      const x = padding + (index / (values.length - 1)) * chartWidth;
      const y = height - padding - ((value - min) / range) * chartHeight;
      
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, 2 * Math.PI);
      ctx.fill();
    });

    // Draw labels
    ctx.fillStyle = '#9CA3AF';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    
    labels.forEach((label, index) => {
      const x = padding + (index / (labels.length - 1)) * chartWidth;
      ctx.fillText(label, x, height - 10);
    });

    // Draw y-axis labels
    ctx.textAlign = 'right';
    for (let i = 0; i <= 5; i++) {
      const value = min + (i / 5) * range;
      const y = height - padding - (i / 5) * chartHeight;
      ctx.fillText(value.toFixed(0), padding - 10, y + 4);
    }
  }

  /**
   * Render bar chart
   */
  private renderBarChart(
    ctx: CanvasRenderingContext2D,
    config: ChartConfiguration,
    width: number,
    height: number
  ): void {
    const padding = 40;
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#374151';
    ctx.fillRect(0, 0, width, height);

    const dataset = config.data.datasets[0];
    const values = dataset.data as number[];
    const labels = config.data.labels;

    if (values.length === 0) return;

    const max = Math.max(...values);
    const barWidth = chartWidth / values.length * 0.8;
    const barSpacing = chartWidth / values.length * 0.2;

    // Draw grid lines
    ctx.strokeStyle = '#4B5563';
    ctx.lineWidth = 1;
    
    for (let i = 0; i <= 5; i++) {
      const y = padding + (i / 5) * chartHeight;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
    }

    // Draw bars
    values.forEach((value, index) => {
      const barHeight = (value / max) * chartHeight;
      const x = padding + index * (barWidth + barSpacing) + barSpacing / 2;
      const y = height - padding - barHeight;

      ctx.fillStyle = Array.isArray(dataset.backgroundColor)
        ? dataset.backgroundColor[index] || '#3B82F6'
        : dataset.backgroundColor || '#3B82F6';

      ctx.fillRect(x, y, barWidth, barHeight);

      // Draw value on top of bar
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(value.toString(), x + barWidth / 2, y - 5);
    });

    // Draw labels
    ctx.fillStyle = '#9CA3AF';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    
    labels.forEach((label, index) => {
      const x = padding + index * (barWidth + barSpacing) + barSpacing / 2 + barWidth / 2;
      ctx.fillText(label, x, height - 10);
    });

    // Draw y-axis labels
    ctx.textAlign = 'right';
    for (let i = 0; i <= 5; i++) {
      const value = (i / 5) * max;
      const y = height - padding - (i / 5) * chartHeight;
      ctx.fillText(value.toFixed(0), padding - 10, y + 4);
    }
  }

  /**
   * Render pie chart
   */
  private renderPieChart(
    ctx: CanvasRenderingContext2D,
    config: ChartConfiguration,
    width: number,
    height: number
  ): void {
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 40;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#374151';
    ctx.fillRect(0, 0, width, height);

    const dataset = config.data.datasets[0];
    const values = dataset.data as number[];
    const labels = config.data.labels;
    const colors = Array.isArray(dataset.backgroundColor)
      ? dataset.backgroundColor
      : ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

    const total = values.reduce((sum, value) => sum + value, 0);
    let currentAngle = -Math.PI / 2;

    // Draw slices
    values.forEach((value, index) => {
      const sliceAngle = (value / total) * 2 * Math.PI;
      
      ctx.fillStyle = colors[index % colors.length];
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
      ctx.closePath();
      ctx.fill();

      // Draw labels
      const labelAngle = currentAngle + sliceAngle / 2;
      const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
      const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);
      
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(`${((value / total) * 100).toFixed(1)}%`, labelX, labelY);

      currentAngle += sliceAngle;
    });

    // Draw legend
    const legendY = height - 60;
    labels.forEach((label, index) => {
      const legendX = 20 + index * 120;
      
      ctx.fillStyle = colors[index % colors.length];
      ctx.fillRect(legendX, legendY, 12, 12);
      
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '12px Arial';
      ctx.textAlign = 'left';
      ctx.fillText(label, legendX + 16, legendY + 9);
    });
  }

  /**
   * Render doughnut chart
   */
  private renderDoughnutChart(
    ctx: CanvasRenderingContext2D,
    config: ChartConfiguration,
    width: number,
    height: number
  ): void {
    const centerX = width / 2;
    const centerY = height / 2;
    const outerRadius = Math.min(width, height) / 2 - 40;
    const innerRadius = outerRadius * 0.5;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#374151';
    ctx.fillRect(0, 0, width, height);

    const dataset = config.data.datasets[0];
    const values = dataset.data as number[];
    const labels = config.data.labels;
    const colors = Array.isArray(dataset.backgroundColor)
      ? dataset.backgroundColor
      : ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

    const total = values.reduce((sum, value) => sum + value, 0);
    let currentAngle = -Math.PI / 2;

    // Draw slices
    values.forEach((value, index) => {
      const sliceAngle = (value / total) * 2 * Math.PI;
      
      ctx.fillStyle = colors[index % colors.length];
      ctx.beginPath();
      ctx.arc(centerX, centerY, outerRadius, currentAngle, currentAngle + sliceAngle);
      ctx.arc(centerX, centerY, innerRadius, currentAngle + sliceAngle, currentAngle, true);
      ctx.closePath();
      ctx.fill();

      currentAngle += sliceAngle;
    });

    // Draw center text
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Total', centerX, centerY - 5);
    ctx.fillText(total.toString(), centerX, centerY + 15);

    // Draw legend
    const legendY = height - 60;
    labels.forEach((label, index) => {
      const legendX = 20 + index * 120;
      
      ctx.fillStyle = colors[index % colors.length];
      ctx.fillRect(legendX, legendY, 12, 12);
      
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '12px Arial';
      ctx.textAlign = 'left';
      ctx.fillText(label, legendX + 16, legendY + 9);
    });
  }

  /**
   * Render area chart
   */
  private renderAreaChart(
    ctx: CanvasRenderingContext2D,
    config: ChartConfiguration,
    width: number,
    height: number
  ): void {
    // Similar to line chart but with filled area
    this.renderLineChart(ctx, config, width, height);

    // Add area fill
    const padding = 40;
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;

    const dataset = config.data.datasets[0];
    const values = dataset.data as number[];

    if (values.length === 0) return;

    const max = Math.max(...values);
    const min = Math.min(...values);
    const range = max - min || 1;

    // Create area path
    ctx.fillStyle = Array.isArray(dataset.backgroundColor) 
      ? dataset.backgroundColor[0] || 'rgba(59, 130, 246, 0.2)'
      : dataset.backgroundColor || 'rgba(59, 130, 246, 0.2)';
    ctx.beginPath();

    // Start from bottom left
    ctx.moveTo(padding, height - padding);

    // Draw line to first point
    const firstY = height - padding - ((values[0] - min) / range) * chartHeight;
    ctx.lineTo(padding, firstY);

    // Draw through all points
    values.forEach((value, index) => {
      const x = padding + (index / (values.length - 1)) * chartWidth;
      const y = height - padding - ((value - min) / range) * chartHeight;
      ctx.lineTo(x, y);
    });

    // Close path at bottom right
    ctx.lineTo(width - padding, height - padding);
    ctx.closePath();
    ctx.fill();
  }

  /**
   * Export chart as image
   */
  exportChart(canvasId: string, format: 'png' | 'jpeg' = 'png'): string | null {
    const instance = this.chartInstances.get(canvasId);
    if (instance) {
      return instance.canvas.toDataURL(`image/${format}`);
    }
    return null;
  }

  /**
   * Get chart statistics
   */
  getChartStats(canvasId: string): ChartStats | null {
    const instance = this.chartInstances.get(canvasId);
    if (instance) {
      const config = instance.config;
      const dataset = config.data.datasets[0];
      const values = dataset.data as number[];
      
      return {
        dataPoints: values.length,
        min: Math.min(...values),
        max: Math.max(...values),
        average: values.reduce((sum, val) => sum + val, 0) / values.length,
        total: values.reduce((sum, val) => sum + val, 0)
      };
    }
    return null;
  }
}

export const chartService = ChartService.getInstance();