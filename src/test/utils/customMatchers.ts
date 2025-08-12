/**
 * Custom Vitest matchers for enhanced testing capabilities
 */

import type { MatcherResult } from 'vitest';
import { expect } from 'vitest';

/**
 * Custom matcher to check if an element has accessible name
 */
function toHaveAccessibleName(
  this: any,
  element: HTMLElement,
  expectedName?: string
): MatcherResult {
  const accessibleName = 
    element.getAttribute('aria-label') ||
    element.getAttribute('aria-labelledby') ||
    element.textContent?.trim() ||
    element.querySelector('[aria-hidden="false"]')?.textContent?.trim() ||
    '';

  const pass = expectedName 
    ? accessibleName === expectedName
    : accessibleName.length > 0;

  return {
    pass,
    message: () => {
      if (expectedName) {
        return `Expected element to have accessible name "${expectedName}", but got "${accessibleName}"`;
      }
      return pass
        ? `Expected element not to have accessible name, but got "${accessibleName}"`
        : `Expected element to have accessible name, but got "${accessibleName}"`;
    },
  };
}

/**
 * Custom matcher to check if an element is focusable
 */
function toBeFocusable(this: any, element: HTMLElement): MatcherResult {
  const focusableSelectors = [
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    'a[href]',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]',
  ];

  const isFocusable = focusableSelectors.some(selector => 
    element.matches(selector)
  );

  return {
    pass: isFocusable,
    message: () => 
      isFocusable
        ? `Expected element not to be focusable`
        : `Expected element to be focusable`,
  };
}

/**
 * Custom matcher to check if an element has proper ARIA attributes
 */
function toHaveProperARIA(this: any, element: HTMLElement): MatcherResult {
  const issues: string[] = [];

  // Check for common ARIA issues
  const role = element.getAttribute('role');
  const ariaLabel = element.getAttribute('aria-label');
  const ariaLabelledBy = element.getAttribute('aria-labelledby');
  const ariaDescribedBy = element.getAttribute('aria-describedby');

  // If element has role, check if it's valid
  if (role) {
    const validRoles = [
      'alert', 'alertdialog', 'application', 'article', 'banner', 'button',
      'cell', 'checkbox', 'columnheader', 'combobox', 'complementary',
      'contentinfo', 'definition', 'dialog', 'directory', 'document',
      'feed', 'figure', 'form', 'grid', 'gridcell', 'group', 'heading',
      'img', 'link', 'list', 'listbox', 'listitem', 'log', 'main',
      'marquee', 'math', 'menu', 'menubar', 'menuitem', 'menuitemcheckbox',
      'menuitemradio', 'navigation', 'none', 'note', 'option', 'presentation',
      'progressbar', 'radio', 'radiogroup', 'region', 'row', 'rowgroup',
      'rowheader', 'scrollbar', 'search', 'searchbox', 'separator',
      'slider', 'spinbutton', 'status', 'switch', 'tab', 'table',
      'tablist', 'tabpanel', 'term', 'textbox', 'timer', 'toolbar',
      'tooltip', 'tree', 'treegrid', 'treeitem'
    ];

    if (!validRoles.includes(role)) {
      issues.push(`Invalid ARIA role: ${role}`);
    }
  }

  // Check if aria-labelledby references exist
  if (ariaLabelledBy) {
    const ids = ariaLabelledBy.split(' ');
    ids.forEach(id => {
      if (!document.getElementById(id)) {
        issues.push(`aria-labelledby references non-existent element: ${id}`);
      }
    });
  }

  // Check if aria-describedby references exist
  if (ariaDescribedBy) {
    const ids = ariaDescribedBy.split(' ');
    ids.forEach(id => {
      if (!document.getElementById(id)) {
        issues.push(`aria-describedby references non-existent element: ${id}`);
      }
    });
  }

  const pass = issues.length === 0;

  return {
    pass,
    message: () => 
      pass
        ? `Expected element to have ARIA issues`
        : `Element has ARIA issues: ${issues.join(', ')}`,
  };
}

/**
 * Custom matcher to check if an error object matches expected structure
 */
function toMatchErrorStructure(
  this: any,
  error: any,
  expectedStructure: Record<string, any>
): MatcherResult {
  const issues: string[] = [];

  // Check required properties
  Object.keys(expectedStructure).forEach(key => {
    if (!(key in error)) {
      issues.push(`Missing property: ${key}`);
    } else if (typeof error[key] !== typeof expectedStructure[key]) {
      issues.push(`Property ${key} has wrong type: expected ${typeof expectedStructure[key]}, got ${typeof error[key]}`);
    }
  });

  // Check for standard error properties
  const standardProperties = ['id', 'type', 'code', 'message', 'severity', 'timestamp'];
  standardProperties.forEach(prop => {
    if (!(prop in error)) {
      issues.push(`Missing standard error property: ${prop}`);
    }
  });

  const pass = issues.length === 0;

  return {
    pass,
    message: () => 
      pass
        ? `Expected error not to match structure`
        : `Error structure issues: ${issues.join(', ')}`,
  };
}

/**
 * Custom matcher to check if a component renders without accessibility violations
 */
function toBeAccessible(this: any, element: HTMLElement): MatcherResult {
  const violations: string[] = [];

  // Check for images without alt text
  const images = element.querySelectorAll('img');
  images.forEach((img, index) => {
    if (!img.getAttribute('alt') && img.getAttribute('role') !== 'presentation') {
      violations.push(`Image at index ${index} missing alt text`);
    }
  });

  // Check for buttons without accessible names
  const buttons = element.querySelectorAll('button');
  buttons.forEach((button, index) => {
    const hasAccessibleName = 
      button.getAttribute('aria-label') ||
      button.getAttribute('aria-labelledby') ||
      button.textContent?.trim();
    
    if (!hasAccessibleName) {
      violations.push(`Button at index ${index} missing accessible name`);
    }
  });

  // Check for form inputs without labels
  const inputs = element.querySelectorAll('input:not([type="hidden"]), textarea, select');
  inputs.forEach((input, index) => {
    const hasLabel = 
      input.getAttribute('aria-label') ||
      input.getAttribute('aria-labelledby') ||
      element.querySelector(`label[for="${input.id}"]`) ||
      input.closest('label');
    
    if (!hasLabel) {
      violations.push(`Input at index ${index} missing label`);
    }
  });

  // Check for proper heading hierarchy
  const headings = Array.from(element.querySelectorAll('h1, h2, h3, h4, h5, h6'));
  if (headings.length > 0) {
    let previousLevel = 0;
    headings.forEach((heading, index) => {
      const level = parseInt(heading.tagName.charAt(1));
      if (index === 0 && level !== 1) {
        violations.push(`First heading should be h1, but found ${heading.tagName.toLowerCase()}`);
      } else if (level > previousLevel + 1) {
        violations.push(`Heading hierarchy skip: ${heading.tagName.toLowerCase()} follows h${previousLevel}`);
      }
      previousLevel = level;
    });
  }

  const pass = violations.length === 0;

  return {
    pass,
    message: () => 
      pass
        ? `Expected element to have accessibility violations`
        : `Accessibility violations found: ${violations.join(', ')}`,
  };
}

/**
 * Custom matcher to check if a mock function was called with type-safe arguments
 */
function toHaveBeenCalledWithTypes<T extends any[]>(
  this: any,
  mockFn: any,
  ...expectedArgs: T
): MatcherResult {
  const calls = mockFn.mock?.calls || [];
  
  const matchingCall = calls.find((call: any[]) => {
    if (call.length !== expectedArgs.length) return false;
    
    return call.every((arg, index) => {
      const expected = expectedArgs[index];
      
      // Type checking
      if (typeof arg !== typeof expected) return false;
      
      // Deep equality for objects
      if (typeof arg === 'object' && arg !== null && expected !== null) {
        return JSON.stringify(arg) === JSON.stringify(expected);
      }
      
      return arg === expected;
    });
  });

  const pass = !!matchingCall;

  return {
    pass,
    message: () => {
      if (pass) {
        return `Expected mock function not to have been called with the specified arguments`;
      }
      
      const callsDescription = calls.length === 0 
        ? 'no calls'
        : `calls: ${calls.map((call: any[]) => JSON.stringify(call)).join(', ')}`;
      
      return `Expected mock function to have been called with ${JSON.stringify(expectedArgs)}, but got ${callsDescription}`;
    },
  };
}

/**
 * Custom matcher to check if an async operation completes within timeout
 */
function toCompleteWithin(
  this: any,
  promise: Promise<any>,
  timeout: number
): Promise<MatcherResult> {
  return Promise.race([
    promise.then(() => ({ pass: true, message: () => 'Promise completed within timeout' })),
    new Promise<MatcherResult>(resolve => {
      setTimeout(() => {
        resolve({
          pass: false,
          message: () => `Expected promise to complete within ${timeout}ms, but it timed out`,
        });
      }, timeout);
    }),
  ]);
}

// Extend Vitest's expect with custom matchers
expect.extend({
  toHaveAccessibleName,
  toBeFocusable,
  toHaveProperARIA,
  toMatchErrorStructure,
  toBeAccessible,
  toHaveBeenCalledWithTypes,
  toCompleteWithin,
});

// Type declarations for custom matchers
declare module 'vitest' {
  interface Assertion<T = any> {
    toHaveAccessibleName(expectedName?: string): T;
    toBeFocusable(): T;
    toHaveProperARIA(): T;
    toMatchErrorStructure(expectedStructure: Record<string, any>): T;
    toBeAccessible(): T;
    toHaveBeenCalledWithTypes<Args extends any[]>(...expectedArgs: Args): T;
    toCompleteWithin(timeout: number): Promise<T>;
  }
  
  interface AsymmetricMatchersContaining {
    toHaveAccessibleName(expectedName?: string): any;
    toBeFocusable(): any;
    toHaveProperARIA(): any;
    toMatchErrorStructure(expectedStructure: Record<string, any>): any;
    toBeAccessible(): any;
    toHaveBeenCalledWithTypes<Args extends any[]>(...expectedArgs: Args): any;
    toCompleteWithin(timeout: number): Promise<any>;
  }
}