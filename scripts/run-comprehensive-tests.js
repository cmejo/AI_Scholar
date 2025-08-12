#!/usr/bin/env node

/**
 * Comprehensive test runner for AI Scholar RAG Chatbot
 * Runs unit tests, integration tests, and generates coverage reports
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ANSI color codes for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

// Test configuration
const testConfig = {
  unitTests: {
    command: 'npm run test:unit',
    description: 'Unit Tests',
    required: true,
  },
  integrationTests: {
    command: 'npm run test:integration',
    description: 'Integration Tests',
    required: true,
  },
  coverageTests: {
    command: 'npm run test:coverage',
    description: 'Coverage Analysis',
    required: false,
  },
  typeCheck: {
    command: 'npm run type-check',
    description: 'TypeScript Type Checking',
    required: true,
  },
  lint: {
    command: 'npm run lint',
    description: 'ESLint Analysis',
    required: true,
  },
};

// Utility functions
function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function logHeader(message) {
  const border = '='.repeat(message.length + 4);
  log(`\n${border}`, colors.cyan);
  log(`  ${message}  `, colors.cyan);
  log(`${border}`, colors.cyan);
}

function logStep(step, total, description) {
  log(`\n[${step}/${total}] ${description}`, colors.blue);
}

function logSuccess(message) {
  log(`✅ ${message}`, colors.green);
}

function logError(message) {
  log(`❌ ${message}`, colors.red);
}

function logWarning(message) {
  log(`⚠️  ${message}`, colors.yellow);
}

function runCommand(command, description) {
  try {
    log(`Running: ${command}`, colors.magenta);
    const output = execSync(command, { 
      stdio: 'pipe',
      encoding: 'utf8',
      maxBuffer: 1024 * 1024 * 10, // 10MB buffer
    });
    
    logSuccess(`${description} completed successfully`);
    return { success: true, output };
  } catch (error) {
    logError(`${description} failed`);
    log(error.stdout || error.message, colors.red);
    return { success: false, error: error.message, output: error.stdout };
  }
}

function generateTestReport(results) {
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      total: Object.keys(results).length,
      passed: Object.values(results).filter(r => r.success).length,
      failed: Object.values(results).filter(r => !r.success).length,
    },
    results,
    coverage: null,
  };

  // Try to read coverage data
  try {
    const coveragePath = path.join(process.cwd(), 'coverage', 'coverage-summary.json');
    if (fs.existsSync(coveragePath)) {
      report.coverage = JSON.parse(fs.readFileSync(coveragePath, 'utf8'));
    }
  } catch (error) {
    logWarning('Could not read coverage data');
  }

  // Write report to file
  const reportPath = path.join(process.cwd(), 'test-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  return report;
}

function displaySummary(report) {
  logHeader('TEST SUMMARY');
  
  log(`Total Tests: ${report.summary.total}`, colors.blue);
  log(`Passed: ${report.summary.passed}`, colors.green);
  log(`Failed: ${report.summary.failed}`, colors.red);
  
  if (report.coverage && report.coverage.total) {
    log('\nCoverage Summary:', colors.cyan);
    const { total } = report.coverage;
    log(`  Lines: ${total.lines.pct}%`, colors.blue);
    log(`  Functions: ${total.functions.pct}%`, colors.blue);
    log(`  Branches: ${total.branches.pct}%`, colors.blue);
    log(`  Statements: ${total.statements.pct}%`, colors.blue);
  }

  // Display failed tests
  if (report.summary.failed > 0) {
    log('\nFailed Tests:', colors.red);
    Object.entries(report.results).forEach(([name, result]) => {
      if (!result.success) {
        log(`  - ${name}: ${result.error}`, colors.red);
      }
    });
  }

  log(`\nDetailed report saved to: test-report.json`, colors.cyan);
}

function checkPrerequisites() {
  logHeader('CHECKING PREREQUISITES');
  
  // Check if node_modules exists
  if (!fs.existsSync('node_modules')) {
    logError('node_modules not found. Please run "npm install" first.');
    process.exit(1);
  }
  
  // Check if package.json exists
  if (!fs.existsSync('package.json')) {
    logError('package.json not found. Please run this script from the project root.');
    process.exit(1);
  }
  
  logSuccess('Prerequisites check passed');
}

function cleanupPreviousRuns() {
  logHeader('CLEANUP');
  
  const pathsToClean = [
    'coverage',
    'test-results.json',
    'test-results-unit.json',
    'test-results-integration.json',
    'test-report.json',
  ];
  
  pathsToClean.forEach(pathToClean => {
    if (fs.existsSync(pathToClean)) {
      if (fs.lstatSync(pathToClean).isDirectory()) {
        fs.rmSync(pathToClean, { recursive: true, force: true });
      } else {
        fs.unlinkSync(pathToClean);
      }
      log(`Cleaned: ${pathToClean}`, colors.yellow);
    }
  });
  
  logSuccess('Cleanup completed');
}

async function main() {
  const startTime = Date.now();
  
  logHeader('AI SCHOLAR RAG CHATBOT - COMPREHENSIVE TEST RUNNER');
  
  // Parse command line arguments
  const args = process.argv.slice(2);
  const skipCleanup = args.includes('--skip-cleanup');
  const skipOptional = args.includes('--skip-optional');
  const verbose = args.includes('--verbose');
  
  try {
    // Check prerequisites
    checkPrerequisites();
    
    // Cleanup previous runs
    if (!skipCleanup) {
      cleanupPreviousRuns();
    }
    
    // Run tests
    logHeader('RUNNING TESTS');
    
    const results = {};
    const testEntries = Object.entries(testConfig);
    let step = 1;
    
    for (const [name, config] of testEntries) {
      // Skip optional tests if requested
      if (skipOptional && !config.required) {
        logWarning(`Skipping optional test: ${config.description}`);
        continue;
      }
      
      logStep(step, testEntries.length, config.description);
      
      const result = runCommand(config.command, config.description);
      results[name] = result;
      
      if (verbose && result.output) {
        log('Output:', colors.magenta);
        log(result.output, colors.reset);
      }
      
      // Stop on critical failures
      if (!result.success && config.required) {
        logError(`Critical test failed: ${config.description}`);
        if (!args.includes('--continue-on-error')) {
          break;
        }
      }
      
      step++;
    }
    
    // Generate and display report
    const report = generateTestReport(results);
    displaySummary(report);
    
    // Exit with appropriate code
    const exitCode = report.summary.failed > 0 ? 1 : 0;
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    
    if (exitCode === 0) {
      logSuccess(`All tests completed successfully in ${duration}s`);
    } else {
      logError(`Tests completed with failures in ${duration}s`);
    }
    
    process.exit(exitCode);
    
  } catch (error) {
    logError(`Test runner failed: ${error.message}`);
    process.exit(1);
  }
}

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  logError(`Uncaught exception: ${error.message}`);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logError(`Unhandled rejection at: ${promise}, reason: ${reason}`);
  process.exit(1);
});

// Run the main function
main().catch((error) => {
  logError(`Main function failed: ${error.message}`);
  process.exit(1);
});