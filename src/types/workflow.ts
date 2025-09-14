// Workflow Management Types

export interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'inactive' | 'error' | 'draft';
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
  lastRun?: Date;
  nextRun?: Date;
  triggers: WorkflowTrigger[];
  conditions: WorkflowCondition[];
  actions: WorkflowAction[];
  schedule?: WorkflowSchedule;
  tags: string[];
  version: number;
  isTemplate: boolean;
}

export interface WorkflowTrigger {
  id: string;
  type: 'manual' | 'schedule' | 'document_upload' | 'api_call' | 'webhook';
  config: Record<string, unknown>;
  enabled: boolean;
}

export interface WorkflowCondition {
  id: string;
  type: 'document_size' | 'document_type' | 'user_role' | 'time_of_day' | 'custom';
  operator: 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'contains' | 'matches';
  value: unknown;
  field?: string;
}

export interface WorkflowAction {
  id: string;
  type: 'auto_tag' | 'send_notification' | 'generate_summary' | 'update_metadata' | 'create_backup' | 'api_call' | 'transform_data';
  name: string;
  config: Record<string, unknown>;
  enabled: boolean;
  order: number;
}

export interface WorkflowSchedule {
  type: 'once' | 'recurring';
  startDate: Date;
  endDate?: Date;
  cron?: string;
  timezone: string;
  enabled: boolean;
}

export interface WorkflowExecution {
  id: string;
  workflowId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  startTime: Date;
  endTime?: Date;
  duration?: number;
  triggeredBy: string;
  triggerType: WorkflowTrigger['type'];
  logs: WorkflowExecutionLog[];
  results: WorkflowExecutionResult[];
  error?: string;
  context: Record<string, unknown>;
}

export interface WorkflowExecutionLog {
  id: string;
  timestamp: Date;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  actionId?: string;
  context?: Record<string, unknown>;
}

export interface WorkflowExecutionResult {
  actionId: string;
  actionName: string;
  status: 'success' | 'failed' | 'skipped';
  result?: unknown;
  error?: string;
  duration: number;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  definition: Omit<WorkflowDefinition, 'id' | 'createdBy' | 'createdAt' | 'updatedAt'>;
  popularity: number;
  isOfficial: boolean;
}

export interface WorkflowStats {
  totalWorkflows: number;
  activeWorkflows: number;
  pausedWorkflows: number;
  errorWorkflows: number;
  totalExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  averageExecutionTime: number;
  executionsToday: number;
  scheduledExecutions: number;
}

export interface WorkflowFilter {
  status?: WorkflowDefinition['status'][];
  createdBy?: string[];
  tags?: string[];
  dateRange?: {
    start: Date;
    end: Date;
  };
  search?: string;
}

export interface WorkflowSort {
  field: 'name' | 'createdAt' | 'updatedAt' | 'lastRun' | 'status';
  direction: 'asc' | 'desc';
}

// Workflow Builder Types
export interface WorkflowNode {
  id: string;
  type: 'trigger' | 'condition' | 'action';
  position: { x: number; y: number };
  data: WorkflowTrigger | WorkflowCondition | WorkflowAction;
  connections: WorkflowConnection[];
}

export interface WorkflowConnection {
  id: string;
  sourceNodeId: string;
  targetNodeId: string;
  type: 'success' | 'failure' | 'conditional';
  condition?: string;
}

export interface WorkflowCanvas {
  nodes: WorkflowNode[];
  connections: WorkflowConnection[];
  zoom: number;
  pan: { x: number; y: number };
}