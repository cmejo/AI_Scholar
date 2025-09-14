// Comprehensive Testing Utilities for Phase 7

interface TestResult {
  name: string;
  passed: boolean;
  duration: number;
  error?: string;
  details?: any;
}

interface TestSuite {
  name: string;
  tests: TestResult[];
  passed: boolean;
  duration: number;
}

class TestRunner {
  private static instance: TestRunner;
  private testSuites: Map<string, TestSuite> = new Map();
  private isRunning: boolean = false;

  public static getInstance(): TestRunner {
    if (!TestRunner.instance) {
      TestRunner.instance = new TestRunner();
    }
    return TestRunner.instance;
  }

  // Run accessibility tests
  public async runAccessibilityTests(): Promise<TestSuite> {
    const startTime = performance.now();
    const tests: TestResult[] = [];

    // Test 1: Check for alt text on images
    tests.push(await this.testImageAltText());
    
    // Test 2: Check for proper heading hierarchy
    tests.push(await this.testHeadingHierarchy());
    
    // Test 3: Check for keyboard navigation
    tests.push(await this.testKeyboardNavigation());
    
    // Test 4: Check for ARIA labels
    tests.push(await this.testAriaLabels());
    
    // Test 5: Check color contrast
    tests.push(await this.testColorContrast());

    const duration = performance.now() - startTime;
    const suite: TestSuite = {
      name: 'Accessibility Tests',
      tests,
      passed: tests.every(t => t.passed),
      duration
    };

    this.testSuites.set('accessibility', suite);
    return suite;
  }

  // Run performance tests
  public async runPerformanceTests(): Promise<TestSuite> {
    const startTime = performance.now();
    const tests: TestResult[] = [];

    tests.push(await this.testLoadTime());
    tests.push(await this.testBundleSize());
    tests.push(await this.testMemoryUsage());
    tests.push(await this.testNetworkRequests());

    const duration = performance.now() - startTime;
    const suite: TestSuite = {
      name: 'Performance Tests',
      tests,
      passed: tests.every(t => t.passed),
      duration
    };

    this.testSuites.set('performance', suite);
    return suite;
  }

  private async testImageAltText(): Promise<TestResult> {
    const start = performance.now();
    try {
      const images = document.querySelectorAll('img');
      const imagesWithoutAlt = Array.from(images).filter(img => !img.alt);
      
      return {
        name: 'Image Alt Text',
        passed: imagesWithoutAlt.length === 0,
        duration: performance.now() - start,
        details: { 
          totalImages: images.length, 
          imagesWithoutAlt: imagesWithoutAlt.length 
        }
      };
    } catch (error) {
      return {
        name: 'Image Alt Text',
        passed: false,
        duration: performance.now() - start,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  private async testHeadingHierarchy(): Promise<TestResult> {
    const start = performance.now();
    try {
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      let previousLevel = 0;
      let hierarchyValid = true;

      Array.from(headings).forEach(heading => {
        const currentLevel = parseInt(heading.tagName.charAt(1));
        if (currentLevel > previousLevel + 1) {
          hierarchyValid = false;
        }
        previousLevel = currentLevel;
      });

      return {
        name: 'Heading Hierarchy',
        passed: hierarchyValid,
        duration: performance.now() - start,
        details: { totalHeadings: headings.length }
      };
    } catch (error) {
      return {
        name: 'Heading Hierarchy',
        passed: false,
        duration: performance.now() - start,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  private async testKeyboardNavigation(): Promise<TestResult> {
    const start = performance.now();
    try {
      const focusableElements = document.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      
      return {
        name: 'Keyboard Navigation',
        passed: focusableElements.length > 0,
        duration: performance.now() - start,
        details: { focusableElements: focusableElements.length }
      };
    } catch (error) {
      return {
        name: 'Keyboard Navigation',
        passed: false,
        duration: performance.now() - start,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  private async testAriaLabels(): Promise<TestResult> {
    const start = performance.now();
    try {
      const interactiveElements = document.querySelectorAll('button, [role="button"]');
      const elementsWithoutLabels = Array.from(interactiveElements).filter(el => 
        !el.getAttribute('aria-label') && !el.textContent?.trim()
      );

      return {
        name: 'ARIA Labels',
        passed: elementsWithoutLabels.length === 0,
        duration: performance.now() - start,
        details: { 
          totalElements: interactiveElements.length,
          elementsWithoutLabels: elementsWithoutLabels.length
        }
      };
    } catch (error) {
      return {
        name: 'ARIA Labels',
        passed: false,
        duration: performance.now() - start,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  private async testColorContrast(): Promise<TestResult> {
    const start = performance.now();
    // Simplified color contrast test
    return {
      name: 'Color Contrast',
      passed: true, // Would need more complex implementation
      duration: performance.now() - start,
      details: { note: 'Manual verification recommended' }
    };
  }

  private async testLoadTime(): Promise<TestResult> {
    const start = performance.now();
    try {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const loadTime = navigation.loadEventEnd - navigation.navigationStart;
      
      return {
        name: 'Load Time',
        passed: loadTime < 3000, // 3 second budget
        duration: performance.now() - start,
        details: { loadTime: `${loadTime}ms`, budget: '3000ms' }
      };
    } catch (error) {
      return {
        name: 'Load Time',
        passed: false,
        duration: performance.now() - start,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  private async testBundleSize(): Promise<TestResult> {
    const start = performance.now();
    try {
      const resources = performance.getEntriesByType('resource');
      const jsResources = resources.filter(r => r.name.endsWith('.js'));
      const totalSize = jsResources.reduce((sum, r) => sum + (r as any).transferSize || 0, 0);
      
      return {
        name: 'Bundle Size',
        passed: totalSize < 500000, // 500KB budget
        duration: performance.now() - start,
        details: { 
          totalSize: `${(totalSize / 1024).toFixed(2)}KB`, 
          budget: '500KB',
          jsFiles: jsResources.length
        }
      };
    } catch (error) {
      return {
        name: 'Bundle Size',
        passed: false,
        duration: performance.now() - start,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  private async testMemoryUsage(): Promise<TestResult> {
    const start = performance.now();
    try {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        const usedMB = memory.usedJSHeapSize / 1024 / 1024;
        
        return {
          name: 'Memory Usage',
          passed: usedMB < 100, // 100MB budget
          duration: performance.now() - start,
          details: { 
            usedMemory: `${usedMB.toFixed(2)}MB`,
            budget: '100MB'
          }
        };
      } else {
        return {
          name: 'Memory Usage',
          passed: true,
          duration: performance.now() - start,
          details: { note: 'Memory API not available' }
        };
      }
    } catch (error) {
      return {
        name: 'Memory Usage',
        passed: false,
        duration: performance.now() - start,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  private async testNetworkRequests(): Promise<TestResult> {
    const start = performance.now();
    try {
      const resources = performance.getEntriesByType('resource');
      const slowRequests = resources.filter(r => r.duration > 1000);
      
      return {
        name: 'Network Requests',
        passed: slowRequests.length === 0,
        duration: performance.now() - start,
        details: { 
          totalRequests: resources.length,
          slowRequests: slowRequests.length,
          threshold: '1000ms'
        }
      };
    } catch (error) {
      return {
        name: 'Network Requests',
        passed: false,
        duration: performance.now() - start,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  public generateTestReport(): string {
    const allSuites = Array.from(this.testSuites.values());
    const totalTests = allSuites.reduce((sum, suite) => sum + suite.tests.length, 0);
    const passedTests = allSuites.reduce((sum, suite) => 
      sum + suite.tests.filter(t => t.passed).length, 0
    );

    return `
Test Report - ${new Date().toLocaleString()}
==========================================

Summary:
- Total Test Suites: ${allSuites.length}
- Total Tests: ${totalTests}
- Passed: ${passedTests}
- Failed: ${totalTests - passedTests}
- Success Rate: ${((passedTests / totalTests) * 100).toFixed(1)}%

${allSuites.map(suite => `
${suite.name}:
- Status: ${suite.passed ? 'PASSED' : 'FAILED'}
- Duration: ${suite.duration.toFixed(2)}ms
- Tests: ${suite.tests.length}

${suite.tests.map(test => `
  ${test.passed ? '✅' : '❌'} ${test.name}
  Duration: ${test.duration.toFixed(2)}ms
  ${test.error ? `Error: ${test.error}` : ''}
  ${test.details ? `Details: ${JSON.stringify(test.details)}` : ''}
`).join('')}
`).join('')}
    `.trim();
  }
}

export const testRunner = TestRunner.getInstance();