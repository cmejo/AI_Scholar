#!/usr/bin/env node

/**
 * Comprehensive Test Coverage Reporter
 * Generates detailed coverage reports and analysis
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class TestCoverageReporter {
  constructor() {
    this.projectRoot = path.resolve(__dirname, '..');
    this.coverageDir = path.join(this.projectRoot, 'coverage');
    this.reportsDir = path.join(this.projectRoot, 'test-reports');
    this.timestamp = new Date().toISOString();
  }

  async generateReport() {
    console.log('🧪 Generating comprehensive test coverage report...');

    try {
      // Ensure reports directory exists
      if (!fs.existsSync(this.reportsDir)) {
        fs.mkdirSync(this.reportsDir, { recursive: true });
      }

      // Read coverage data
      const coverageData = await this.readCoverageData();
      
      // Generate reports
      const summary = this.generateSummaryReport(coverageData);
      const detailed = this.generateDetailedReport(coverageData);
      const trends = await this.generateTrendsReport(coverageData);
      const recommendations = this.generateRecommendations(coverageData);

      // Write reports
      await this.writeReports({
        summary,
        detailed,
        trends,
        recommendations,
        coverageData
      });

      console.log('✅ Coverage reports generated successfully!');
      console.log(`📊 Reports available in: ${this.reportsDir}`);

    } catch (error) {
      console.error('❌ Failed to generate coverage report:', error);
      process.exit(1);
    }
  }

  async readCoverageData() {
    const coverageFiles = [
      path.join(this.coverageDir, 'coverage-summary.json'),
      path.join(this.coverageDir, 'coverage-final.json'),
      path.join(this.projectRoot, 'test-results.json')
    ];

    const data = {};

    for (const file of coverageFiles) {
      if (fs.existsSync(file)) {
        try {
          const content = fs.readFileSync(file, 'utf8');
          const filename = path.basename(file, '.json');
          data[filename] = JSON.parse(content);
        } catch (error) {
          console.warn(`⚠️  Could not read ${file}:`, error.message);
        }
      }
    }

    return data;
  }

  generateSummaryReport(coverageData) {
    const summary = coverageData['coverage-summary'];
    if (!summary) {
      return { error: 'No coverage summary data available' };
    }

    const total = summary.total || {};
    
    return {
      timestamp: this.timestamp,
      overall: {
        statements: this.formatCoverageMetric(total.statements),
        branches: this.formatCoverageMetric(total.branches),
        functions: this.formatCoverageMetric(total.functions),
        lines: this.formatCoverageMetric(total.lines)
      },
      thresholds: {
        global: {
          statements: 80,
          branches: 75,
          functions: 80,
          lines: 80
        },
        components: {
          statements: 75,
          branches: 70,
          functions: 75,
          lines: 75
        },
        services: {
          statements: 85,
          branches: 80,
          functions: 85,
          lines: 85
        },
        utils: {
          statements: 90,
          branches: 85,
          functions: 90,
          lines: 90
        }
      },
      status: this.calculateOverallStatus(total),
      recommendations: this.getQuickRecommendations(total)
    };
  }

  generateDetailedReport(coverageData) {
    const summary = coverageData['coverage-summary'];
    if (!summary) {
      return { error: 'No detailed coverage data available' };
    }

    const fileReports = {};
    const categoryReports = {
      components: { files: [], totals: { statements: 0, branches: 0, functions: 0, lines: 0 } },
      services: { files: [], totals: { statements: 0, branches: 0, functions: 0, lines: 0 } },
      utils: { files: [], totals: { statements: 0, branches: 0, functions: 0, lines: 0 } },
      hooks: { files: [], totals: { statements: 0, branches: 0, functions: 0, lines: 0 } },
      types: { files: [], totals: { statements: 0, branches: 0, functions: 0, lines: 0 } },
      contexts: { files: [], totals: { statements: 0, branches: 0, functions: 0, lines: 0 } }
    };

    // Process each file
    Object.entries(summary).forEach(([filePath, data]) => {
      if (filePath === 'total') return;

      const fileReport = {
        path: filePath,
        statements: this.formatCoverageMetric(data.statements),
        branches: this.formatCoverageMetric(data.branches),
        functions: this.formatCoverageMetric(data.functions),
        lines: this.formatCoverageMetric(data.lines),
        uncoveredLines: data.lines?.uncoveredLines || [],
        status: this.calculateFileStatus(data)
      };

      fileReports[filePath] = fileReport;

      // Categorize file
      const category = this.categorizeFile(filePath);
      if (categoryReports[category]) {
        categoryReports[category].files.push(fileReport);
        this.addToTotals(categoryReports[category].totals, data);
      }
    });

    // Calculate category averages
    Object.keys(categoryReports).forEach(category => {
      const cat = categoryReports[category];
      if (cat.files.length > 0) {
        cat.average = {
          statements: cat.totals.statements / cat.files.length,
          branches: cat.totals.branches / cat.files.length,
          functions: cat.totals.functions / cat.files.length,
          lines: cat.totals.lines / cat.files.length
        };
      }
    });

    return {
      timestamp: this.timestamp,
      files: fileReports,
      categories: categoryReports,
      lowCoverageFiles: this.findLowCoverageFiles(fileReports),
      highCoverageFiles: this.findHighCoverageFiles(fileReports)
    };
  }

  async generateTrendsReport(coverageData) {
    const trendsFile = path.join(this.reportsDir, 'coverage-trends.json');
    let trends = [];

    // Load existing trends
    if (fs.existsSync(trendsFile)) {
      try {
        trends = JSON.parse(fs.readFileSync(trendsFile, 'utf8'));
      } catch (error) {
        console.warn('Could not load existing trends:', error.message);
      }
    }

    // Add current data point
    const summary = coverageData['coverage-summary'];
    if (summary && summary.total) {
      const currentPoint = {
        timestamp: this.timestamp,
        date: new Date().toISOString().split('T')[0],
        statements: summary.total.statements?.pct || 0,
        branches: summary.total.branches?.pct || 0,
        functions: summary.total.functions?.pct || 0,
        lines: summary.total.lines?.pct || 0
      };

      trends.push(currentPoint);

      // Keep only last 30 data points
      if (trends.length > 30) {
        trends = trends.slice(-30);
      }

      // Save updated trends
      fs.writeFileSync(trendsFile, JSON.stringify(trends, null, 2));
    }

    return {
      data: trends,
      analysis: this.analyzeTrends(trends)
    };
  }

  generateRecommendations(coverageData) {
    const summary = coverageData['coverage-summary'];
    const recommendations = [];

    if (!summary) {
      return [{ type: 'error', message: 'No coverage data available for analysis' }];
    }

    const total = summary.total || {};

    // Overall coverage recommendations
    if (total.statements?.pct < 80) {
      recommendations.push({
        type: 'critical',
        category: 'overall',
        message: `Statement coverage is ${total.statements?.pct}%, below the 80% threshold`,
        action: 'Add unit tests for uncovered statements',
        priority: 'high'
      });
    }

    if (total.branches?.pct < 75) {
      recommendations.push({
        type: 'warning',
        category: 'overall',
        message: `Branch coverage is ${total.branches?.pct}%, below the 75% threshold`,
        action: 'Add tests for conditional logic and error paths',
        priority: 'medium'
      });
    }

    if (total.functions?.pct < 80) {
      recommendations.push({
        type: 'warning',
        category: 'overall',
        message: `Function coverage is ${total.functions?.pct}%, below the 80% threshold`,
        action: 'Add tests for untested functions',
        priority: 'high'
      });
    }

    // File-specific recommendations
    Object.entries(summary).forEach(([filePath, data]) => {
      if (filePath === 'total') return;

      const category = this.categorizeFile(filePath);
      const thresholds = this.getThresholdsForCategory(category);

      if (data.statements?.pct < thresholds.statements) {
        recommendations.push({
          type: 'file',
          category,
          file: filePath,
          message: `Low statement coverage: ${data.statements?.pct}%`,
          action: `Add unit tests to reach ${thresholds.statements}% threshold`,
          priority: this.getPriority(data.statements?.pct, thresholds.statements)
        });
      }

      if (data.lines?.uncoveredLines?.length > 10) {
        recommendations.push({
          type: 'file',
          category,
          file: filePath,
          message: `${data.lines.uncoveredLines.length} uncovered lines`,
          action: 'Focus on testing the most critical uncovered code paths',
          priority: 'medium'
        });
      }
    });

    // Test quality recommendations
    const testResults = coverageData['test-results'];
    if (testResults) {
      if (testResults.numFailedTests > 0) {
        recommendations.push({
          type: 'critical',
          category: 'quality',
          message: `${testResults.numFailedTests} failing tests`,
          action: 'Fix failing tests before focusing on coverage',
          priority: 'critical'
        });
      }

      if (testResults.numPendingTests > 5) {
        recommendations.push({
          type: 'warning',
          category: 'quality',
          message: `${testResults.numPendingTests} pending/skipped tests`,
          action: 'Complete or remove pending tests',
          priority: 'low'
        });
      }
    }

    return recommendations.sort((a, b) => {
      const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    });
  }

  async writeReports(reports) {
    const files = [
      {
        name: 'coverage-summary.json',
        content: JSON.stringify(reports.summary, null, 2)
      },
      {
        name: 'coverage-detailed.json',
        content: JSON.stringify(reports.detailed, null, 2)
      },
      {
        name: 'coverage-recommendations.json',
        content: JSON.stringify(reports.recommendations, null, 2)
      },
      {
        name: 'coverage-report.md',
        content: this.generateMarkdownReport(reports)
      },
      {
        name: 'coverage-dashboard.html',
        content: this.generateHTMLDashboard(reports)
      }
    ];

    for (const file of files) {
      const filePath = path.join(this.reportsDir, file.name);
      fs.writeFileSync(filePath, file.content);
      console.log(`📄 Generated: ${file.name}`);
    }
  }

  generateMarkdownReport(reports) {
    const { summary, detailed, recommendations } = reports;
    
    return `# Test Coverage Report

Generated: ${this.timestamp}

## Overall Coverage

| Metric | Coverage | Threshold | Status |
|--------|----------|-----------|--------|
| Statements | ${summary.overall.statements.pct}% | 80% | ${summary.overall.statements.pct >= 80 ? '✅' : '❌'} |
| Branches | ${summary.overall.branches.pct}% | 75% | ${summary.overall.branches.pct >= 75 ? '✅' : '❌'} |
| Functions | ${summary.overall.functions.pct}% | 80% | ${summary.overall.functions.pct >= 80 ? '✅' : '❌'} |
| Lines | ${summary.overall.lines.pct}% | 80% | ${summary.overall.lines.pct >= 80 ? '✅' : '❌'} |

## Category Breakdown

${Object.entries(detailed.categories).map(([category, data]) => {
  if (data.files.length === 0) return '';
  return `### ${category.charAt(0).toUpperCase() + category.slice(1)}
- Files: ${data.files.length}
- Average Coverage: ${data.average ? Math.round(data.average.statements) : 0}%`;
}).filter(Boolean).join('\n\n')}

## Recommendations

${recommendations.slice(0, 10).map((rec, index) => 
  `${index + 1}. **${rec.type.toUpperCase()}** (${rec.priority}): ${rec.message}
   - Action: ${rec.action}${rec.file ? `\n   - File: \`${rec.file}\`` : ''}`
).join('\n\n')}

## Low Coverage Files

${detailed.lowCoverageFiles.slice(0, 10).map(file => 
  `- \`${file.path}\` - ${file.statements.pct}% statements`
).join('\n')}

---
*Report generated by Test Coverage Reporter*
`;
  }

  generateHTMLDashboard(reports) {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Coverage Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric { background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; margin-bottom: 10px; }
        .metric-label { color: #666; font-size: 0.9em; }
        .status-good { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-bad { color: #dc3545; }
        .recommendations { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .recommendation { padding: 10px; margin: 10px 0; border-left: 4px solid #007bff; background: #f8f9fa; }
        .recommendation.critical { border-color: #dc3545; }
        .recommendation.warning { border-color: #ffc107; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Test Coverage Dashboard</h1>
            <p>Generated: ${this.timestamp}</p>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value ${this.getStatusClass(reports.summary.overall.statements.pct, 80)}">${reports.summary.overall.statements.pct}%</div>
                <div class="metric-label">Statements</div>
            </div>
            <div class="metric">
                <div class="metric-value ${this.getStatusClass(reports.summary.overall.branches.pct, 75)}">${reports.summary.overall.branches.pct}%</div>
                <div class="metric-label">Branches</div>
            </div>
            <div class="metric">
                <div class="metric-value ${this.getStatusClass(reports.summary.overall.functions.pct, 80)}">${reports.summary.overall.functions.pct}%</div>
                <div class="metric-label">Functions</div>
            </div>
            <div class="metric">
                <div class="metric-value ${this.getStatusClass(reports.summary.overall.lines.pct, 80)}">${reports.summary.overall.lines.pct}%</div>
                <div class="metric-label">Lines</div>
            </div>
        </div>
        
        <div class="recommendations">
            <h2>Top Recommendations</h2>
            ${reports.recommendations.slice(0, 5).map(rec => 
              `<div class="recommendation ${rec.type}">
                <strong>${rec.type.toUpperCase()}</strong> (${rec.priority}): ${rec.message}
                <br><small>Action: ${rec.action}</small>
              </div>`
            ).join('')}
        </div>
    </div>
</body>
</html>`;
  }

  // Helper methods
  formatCoverageMetric(metric) {
    if (!metric) return { pct: 0, covered: 0, total: 0 };
    return {
      pct: Math.round(metric.pct || 0),
      covered: metric.covered || 0,
      total: metric.total || 0
    };
  }

  calculateOverallStatus(total) {
    const scores = [
      total.statements?.pct || 0,
      total.branches?.pct || 0,
      total.functions?.pct || 0,
      total.lines?.pct || 0
    ];
    const average = scores.reduce((a, b) => a + b, 0) / scores.length;
    
    if (average >= 85) return 'excellent';
    if (average >= 75) return 'good';
    if (average >= 60) return 'fair';
    return 'poor';
  }

  calculateFileStatus(data) {
    const scores = [
      data.statements?.pct || 0,
      data.branches?.pct || 0,
      data.functions?.pct || 0,
      data.lines?.pct || 0
    ];
    const average = scores.reduce((a, b) => a + b, 0) / scores.length;
    return average >= 80 ? 'good' : average >= 60 ? 'fair' : 'poor';
  }

  categorizeFile(filePath) {
    if (filePath.includes('/components/')) return 'components';
    if (filePath.includes('/services/')) return 'services';
    if (filePath.includes('/utils/')) return 'utils';
    if (filePath.includes('/hooks/')) return 'hooks';
    if (filePath.includes('/types/')) return 'types';
    if (filePath.includes('/contexts/')) return 'contexts';
    return 'other';
  }

  getThresholdsForCategory(category) {
    const thresholds = {
      components: { statements: 75, branches: 70, functions: 75, lines: 75 },
      services: { statements: 85, branches: 80, functions: 85, lines: 85 },
      utils: { statements: 90, branches: 85, functions: 90, lines: 90 },
      hooks: { statements: 85, branches: 80, functions: 85, lines: 85 },
      types: { statements: 95, branches: 95, functions: 95, lines: 95 },
      contexts: { statements: 80, branches: 75, functions: 80, lines: 80 }
    };
    return thresholds[category] || { statements: 80, branches: 75, functions: 80, lines: 80 };
  }

  getPriority(current, threshold) {
    const diff = threshold - current;
    if (diff > 30) return 'critical';
    if (diff > 15) return 'high';
    if (diff > 5) return 'medium';
    return 'low';
  }

  getStatusClass(value, threshold) {
    if (value >= threshold) return 'status-good';
    if (value >= threshold - 10) return 'status-warning';
    return 'status-bad';
  }

  findLowCoverageFiles(fileReports) {
    return Object.values(fileReports)
      .filter(file => file.statements.pct < 50)
      .sort((a, b) => a.statements.pct - b.statements.pct);
  }

  findHighCoverageFiles(fileReports) {
    return Object.values(fileReports)
      .filter(file => file.statements.pct >= 90)
      .sort((a, b) => b.statements.pct - a.statements.pct);
  }

  addToTotals(totals, data) {
    totals.statements += data.statements?.pct || 0;
    totals.branches += data.branches?.pct || 0;
    totals.functions += data.functions?.pct || 0;
    totals.lines += data.lines?.pct || 0;
  }

  analyzeTrends(trends) {
    if (trends.length < 2) return { message: 'Insufficient data for trend analysis' };

    const recent = trends.slice(-5);
    const older = trends.slice(-10, -5);

    const recentAvg = recent.reduce((sum, point) => sum + point.statements, 0) / recent.length;
    const olderAvg = older.length > 0 ? older.reduce((sum, point) => sum + point.statements, 0) / older.length : recentAvg;

    const trend = recentAvg - olderAvg;
    
    return {
      direction: trend > 1 ? 'improving' : trend < -1 ? 'declining' : 'stable',
      change: Math.round(trend * 100) / 100,
      message: trend > 1 ? 'Coverage is improving' : trend < -1 ? 'Coverage is declining' : 'Coverage is stable'
    };
  }

  getQuickRecommendations(total) {
    const recommendations = [];
    
    if (total.statements?.pct < 80) {
      recommendations.push('Focus on adding unit tests for core functionality');
    }
    if (total.branches?.pct < 75) {
      recommendations.push('Add tests for conditional logic and error handling');
    }
    if (total.functions?.pct < 80) {
      recommendations.push('Ensure all public functions have tests');
    }
    
    return recommendations;
  }
}

// Run the reporter
if (import.meta.url === `file://${process.argv[1]}`) {
  const reporter = new TestCoverageReporter();
  reporter.generateReport().catch(console.error);
}

export default TestCoverageReporter;