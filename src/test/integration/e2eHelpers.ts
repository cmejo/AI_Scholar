/**
 * End-to-end testing helpers and utilities
 */

import { screen, waitFor } from '@testing-library/react';
import type { UserEvent } from '@testing-library/user-event';
import userEvent from '@testing-library/user-event';
import { expect } from 'vitest';

/**
 * Interface for E2E test scenario
 */
interface E2EScenario {
  name: string;
  description: string;
  steps: E2EStep[];
  expectedOutcome: string;
  timeout?: number;
}

/**
 * Interface for E2E test step
 */
interface E2EStep {
  action: 'navigate' | 'click' | 'type' | 'upload' | 'wait' | 'verify' | 'screenshot';
  target?: string;
  value?: any;
  timeout?: number;
  description: string;
}

/**
 * E2E test runner for complex user workflows
 */
export class E2ETestRunner {
  private user: UserEvent;
  private screenshots: string[] = [];
  private currentStep = 0;

  constructor() {
    this.user = userEvent.setup();
  }

  /**
   * Run a complete E2E scenario
   */
  async runScenario(scenario: E2EScenario): Promise<void> {
    console.log(`Running E2E scenario: ${scenario.name}`);
    console.log(`Description: ${scenario.description}`);

    try {
      for (let i = 0; i < scenario.steps.length; i++) {
        this.currentStep = i + 1;
        const step = scenario.steps[i];
        
        console.log(`Step ${this.currentStep}: ${step.description}`);
        await this.executeStep(step);
      }

      console.log(`✅ Scenario completed: ${scenario.expectedOutcome}`);
    } catch (error) {
      console.error(`❌ Scenario failed at step ${this.currentStep}: ${error}`);
      throw error;
    }
  }

  /**
   * Execute a single E2E step
   */
  private async executeStep(step: E2EStep): Promise<void> {
    const timeout = step.timeout || 5000;

    switch (step.action) {
      case 'navigate':
        await this.navigate(step.target!, timeout);
        break;

      case 'click':
        await this.click(step.target!, timeout);
        break;

      case 'type':
        await this.type(step.target!, step.value, timeout);
        break;

      case 'upload':
        await this.upload(step.target!, step.value, timeout);
        break;

      case 'wait':
        await this.waitFor(step.target!, timeout);
        break;

      case 'verify':
        await this.verify(step.target!, step.value, timeout);
        break;

      case 'screenshot':
        await this.takeScreenshot(step.target || `step-${this.currentStep}`);
        break;

      default:
        throw new Error(`Unknown action: ${step.action}`);
    }
  }

  /**
   * Navigate to a specific route or URL
   */
  private async navigate(target: string, timeout: number): Promise<void> {
    // Mock navigation for testing
    window.history.pushState({}, '', target);
    window.dispatchEvent(new PopStateEvent('popstate'));
    
    await waitFor(() => {
      expect(window.location.pathname).toBe(target);
    }, { timeout });
  }

  /**
   * Click on an element
   */
  private async click(target: string, timeout: number): Promise<void> {
    await waitFor(async () => {
      const element = this.findElement(target);
      expect(element).toBeInTheDocument();
      await this.user.click(element);
    }, { timeout });
  }

  /**
   * Type text into an input field
   */
  private async type(target: string, value: string, timeout: number): Promise<void> {
    await waitFor(async () => {
      const element = this.findElement(target) as HTMLInputElement;
      expect(element).toBeInTheDocument();
      await this.user.clear(element);
      await this.user.type(element, value);
    }, { timeout });
  }

  /**
   * Upload a file
   */
  private async upload(target: string, file: File, timeout: number): Promise<void> {
    await waitFor(async () => {
      const element = this.findElement(target) as HTMLInputElement;
      expect(element).toBeInTheDocument();
      await this.user.upload(element, file);
    }, { timeout });
  }

  /**
   * Wait for an element or condition
   */
  private async waitFor(target: string, timeout: number): Promise<void> {
    await waitFor(() => {
      const element = this.findElement(target);
      expect(element).toBeInTheDocument();
    }, { timeout });
  }

  /**
   * Verify an element or condition
   */
  private async verify(target: string, expectedValue: any, timeout: number): Promise<void> {
    await waitFor(() => {
      const element = this.findElement(target);
      
      if (typeof expectedValue === 'string') {
        expect(element).toHaveTextContent(expectedValue);
      } else if (typeof expectedValue === 'boolean') {
        if (expectedValue) {
          expect(element).toBeInTheDocument();
        } else {
          expect(element).not.toBeInTheDocument();
        }
      } else if (expectedValue && typeof expectedValue === 'object') {
        Object.entries(expectedValue).forEach(([attr, value]) => {
          expect(element).toHaveAttribute(attr, value as string);
        });
      }
    }, { timeout });
  }

  /**
   * Take a screenshot (mock implementation)
   */
  private async takeScreenshot(name: string): Promise<void> {
    // In a real E2E environment, this would capture an actual screenshot
    const screenshot = `screenshot-${name}-${Date.now()}.png`;
    this.screenshots.push(screenshot);
    console.log(`📸 Screenshot taken: ${screenshot}`);
  }

  /**
   * Find an element by various selectors
   */
  private findElement(target: string): HTMLElement {
    // Try different strategies to find the element
    let element: HTMLElement | null = null;

    // Try by test ID
    element = screen.queryByTestId(target);
    if (element) return element;

    // Try by role and name
    const roleMatch = target.match(/^(\w+):(.+)$/);
    if (roleMatch) {
      const [, role, name] = roleMatch;
      element = screen.queryByRole(role as any, { name: new RegExp(name, 'i') });
      if (element) return element;
    }

    // Try by text content
    element = screen.queryByText(new RegExp(target, 'i'));
    if (element) return element;

    // Try by label
    element = screen.queryByLabelText(new RegExp(target, 'i'));
    if (element) return element;

    // Try by placeholder
    element = screen.queryByPlaceholderText(new RegExp(target, 'i'));
    if (element) return element;

    // Try by CSS selector
    element = document.querySelector(target);
    if (element) return element as HTMLElement;

    throw new Error(`Element not found: ${target}`);
  }

  /**
   * Get all screenshots taken during the test
   */
  getScreenshots(): string[] {
    return [...this.screenshots];
  }

  /**
   * Clean up resources
   */
  cleanup(): void {
    this.screenshots = [];
    this.currentStep = 0;
  }
}

/**
 * Pre-defined E2E scenarios for common workflows
 */
export const commonE2EScenarios: Record<string, E2EScenario> = {
  chatWorkflow: {
    name: 'Complete Chat Workflow',
    description: 'User sends a message and receives a response',
    steps: [
      {
        action: 'navigate',
        target: '/chat',
        description: 'Navigate to chat page',
      },
      {
        action: 'wait',
        target: 'textbox',
        description: 'Wait for chat input to be available',
      },
      {
        action: 'type',
        target: 'textbox',
        value: 'What is machine learning?',
        description: 'Type a question in the chat input',
      },
      {
        action: 'click',
        target: 'button:Send',
        description: 'Click the send button',
      },
      {
        action: 'wait',
        target: 'machine learning',
        description: 'Wait for AI response to appear',
        timeout: 10000,
      },
      {
        action: 'verify',
        target: 'assistant',
        value: true,
        description: 'Verify assistant response is displayed',
      },
    ],
    expectedOutcome: 'User successfully sends message and receives AI response',
  },

  documentUploadWorkflow: {
    name: 'Document Upload Workflow',
    description: 'User uploads a document and it appears in the document list',
    steps: [
      {
        action: 'navigate',
        target: '/documents',
        description: 'Navigate to documents page',
      },
      {
        action: 'click',
        target: 'button:Upload',
        description: 'Click upload button',
      },
      {
        action: 'upload',
        target: 'file input',
        value: new File(['test content'], 'test.pdf', { type: 'application/pdf' }),
        description: 'Upload a test PDF file',
      },
      {
        action: 'wait',
        target: 'test.pdf',
        description: 'Wait for uploaded file to appear in list',
        timeout: 10000,
      },
      {
        action: 'verify',
        target: 'test.pdf',
        value: true,
        description: 'Verify uploaded document is in the list',
      },
    ],
    expectedOutcome: 'Document is successfully uploaded and appears in document list',
  },

  searchWorkflow: {
    name: 'Search Workflow',
    description: 'User searches for documents and views results',
    steps: [
      {
        action: 'navigate',
        target: '/search',
        description: 'Navigate to search page',
      },
      {
        action: 'type',
        target: 'searchbox',
        value: 'neural networks',
        description: 'Enter search query',
      },
      {
        action: 'click',
        target: 'button:Search',
        description: 'Click search button',
      },
      {
        action: 'wait',
        target: 'search results',
        description: 'Wait for search results to load',
        timeout: 10000,
      },
      {
        action: 'verify',
        target: 'neural networks',
        value: true,
        description: 'Verify search results contain the query term',
      },
    ],
    expectedOutcome: 'Search returns relevant results for the query',
  },

  voiceInteractionWorkflow: {
    name: 'Voice Interaction Workflow',
    description: 'User uses voice input to interact with the system',
    steps: [
      {
        action: 'navigate',
        target: '/chat',
        description: 'Navigate to chat page',
      },
      {
        action: 'click',
        target: 'button:microphone',
        description: 'Click microphone button to start voice input',
      },
      {
        action: 'wait',
        target: 'listening',
        description: 'Wait for voice recognition to start',
      },
      {
        action: 'verify',
        target: 'listening',
        value: true,
        description: 'Verify voice recognition is active',
      },
      {
        action: 'wait',
        target: 'transcription',
        description: 'Wait for speech transcription',
        timeout: 10000,
      },
      {
        action: 'verify',
        target: 'transcription',
        value: true,
        description: 'Verify speech was transcribed',
      },
    ],
    expectedOutcome: 'Voice input is successfully transcribed and processed',
  },

  errorHandlingWorkflow: {
    name: 'Error Handling Workflow',
    description: 'System gracefully handles and displays errors',
    steps: [
      {
        action: 'navigate',
        target: '/chat',
        description: 'Navigate to chat page',
      },
      {
        action: 'click',
        target: 'button:trigger-error',
        description: 'Trigger an error condition',
      },
      {
        action: 'wait',
        target: 'error message',
        description: 'Wait for error message to appear',
      },
      {
        action: 'verify',
        target: 'error message',
        value: true,
        description: 'Verify error message is displayed',
      },
      {
        action: 'click',
        target: 'button:dismiss',
        description: 'Dismiss the error message',
      },
      {
        action: 'verify',
        target: 'error message',
        value: false,
        description: 'Verify error message is dismissed',
      },
    ],
    expectedOutcome: 'Errors are properly displayed and can be dismissed',
  },
};

/**
 * Utility function to run multiple E2E scenarios
 */
export const runE2EScenarios = async (
  scenarios: E2EScenario[],
  options: { parallel?: boolean; stopOnFailure?: boolean } = {}
): Promise<void> => {
  const { parallel = false, stopOnFailure = true } = options;

  if (parallel) {
    const results = await Promise.allSettled(
      scenarios.map(scenario => {
        const runner = new E2ETestRunner();
        return runner.runScenario(scenario).finally(() => runner.cleanup());
      })
    );

    const failures = results.filter(result => result.status === 'rejected');
    if (failures.length > 0 && stopOnFailure) {
      throw new Error(`${failures.length} E2E scenarios failed`);
    }
  } else {
    const runner = new E2ETestRunner();
    
    try {
      for (const scenario of scenarios) {
        await runner.runScenario(scenario);
      }
    } catch (error) {
      if (stopOnFailure) {
        throw error;
      }
    } finally {
      runner.cleanup();
    }
  }
};

/**
 * Utility to create custom E2E scenarios
 */
export const createE2EScenario = (
  name: string,
  description: string,
  steps: E2EStep[],
  expectedOutcome: string,
  timeout?: number
): E2EScenario => {
  return {
    name,
    description,
    steps,
    expectedOutcome,
    timeout,
  };
};

/**
 * Utility to validate E2E scenario structure
 */
export const validateE2EScenario = (scenario: E2EScenario): boolean => {
  if (!scenario.name || !scenario.description || !scenario.expectedOutcome) {
    return false;
  }

  if (!Array.isArray(scenario.steps) || scenario.steps.length === 0) {
    return false;
  }

  return scenario.steps.every(step => 
    step.action && step.description && 
    ['navigate', 'click', 'type', 'upload', 'wait', 'verify', 'screenshot'].includes(step.action)
  );
};