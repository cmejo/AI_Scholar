#!/usr/bin/env node

/**
 * AI Scholar RAG Chatbot - Quality Monitoring Orchestrator
 * 
 * This script orchestrates the complete quality monitoring pipeline including
 * metrics collection, trend analysis, reporting, and alerting.
 */

import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Import quality components
import { QualityConfigValidator } from './quality-config-validator.js';
import { QualityMetricsAggregator } from './quality-metrics-aggregator.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class QualityMonitor {
    constructor(options = {}) {
        this.options = {
            skipValidation: false,
            skipMetrics: false,
            skipDashboard: false,
            skipAlerts: false,
            verbose: false,
            ...options
        };
        
        this.results = {
            validation: null,
            metrics: null,
            dashboard: null,
            alerts: null,
            startTime: Date.now(),
            endTime: null
        };
    }

    async runCompleteMonitoring() {
        console.log('🚀 Starting comprehensive quality monitoring pipeline...');
        console.log('='.repeat(60));
        
        try {
            // Step 1: Validate configuration
            if (!this.options.skipValidation) {
                await this.validateConfiguration();
            }

            // Step 2: Collect comprehensive metrics
            if (!this.options.skipMetrics) {
                await this.collectMetrics();
            }

            // Step 3: Generate dashboard
            if (!this.options.skipDashboard) {
                await this.generateDashboard();
            }

            // Step 4: Run alerts monitoring
            if (!this.options.skipAlerts) {
                await this.runAlerts();
            }

            // Step 5: Generate summary report
            await this.generateSummaryReport();

            this.results.endTime = Date.now();
            this.displayFinalResults();

            return true;
        } catch (error) {
            console.error(`❌ Quality monitoring pipeline failed: ${error.message}`);
            this.results.endTime = Date.now();
            return false;
        }
    }

    async validateConfiguration() {
        console.log('🔍 Step 1: Validating quality configuration...');
        
        try {
            const validator = new QualityConfigValidator();
            const isValid = await validator.validateConfiguration();
            
            this.results.validation = {
                passed: isValid,
                timestamp: new Date().toISOString()
            };

            if (!isValid) {
                console.log('⚠️ Configuration validation failed, but continuing with monitoring...');
            }
        } catch (error) {
            console.error(`❌ Configuration validation error: ${error.message}`);
            this.results.validation = {
                passed: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async collectMetrics() {
        console.log('📊 Step 2: Collecting comprehensive quality metrics...');
        
        try {
            const aggregator = new QualityMetricsAggregator();
            const metrics = await aggregator.collectComprehensiveMetrics();
            
            this.results.metrics = {
                success: true,
                qualityScore: metrics.overall.qualityScore,
                coverage: metrics.overall.coverage,
                totalErrors: metrics.overall.totalErrors,
                alertsCount: metrics.alerts.length,
                timestamp: metrics.timestamp
            };

            console.log(`✅ Metrics collected - Quality Score: ${metrics.overall.qualityScore}/100`);
        } catch (error) {
            console.error(`❌ Metrics collection error: ${error.message}`);
            this.results.metrics = {
                success: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async generateDashboard() {
        console.log('📈 Step 3: Generating interactive quality dashboard...');
        
        try {
            const result = await this.runPythonScript('quality-dashboard.py');
            
            this.results.dashboard = {
                success: result.success,
                timestamp: new Date().toISOString()
            };

            if (result.success) {
                console.log('✅ Quality dashboard generated successfully');
            } else {
                console.error(`❌ Dashboard generation failed: ${result.error}`);
            }
        } catch (error) {
            console.error(`❌ Dashboard generation error: ${error.message}`);
            this.results.dashboard = {
                success: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async runAlerts() {
        console.log('🚨 Step 4: Running quality alerts monitoring...');
        
        try {
            const result = await this.runPythonScript('quality-alerts.py');
            
            this.results.alerts = {
                success: result.success,
                timestamp: new Date().toISOString()
            };

            if (result.success) {
                console.log('✅ Quality alerts monitoring completed');
            } else {
                console.error(`❌ Alerts monitoring failed: ${result.error}`);
            }
        } catch (error) {
            console.error(`❌ Alerts monitoring error: ${error.message}`);
            this.results.alerts = {
                success: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async runPythonScript(scriptName) {
        return new Promise((resolve) => {
            const scriptPath = path.join('scripts', scriptName);
            
            if (!fs.existsSync(scriptPath)) {
                resolve({ success: false, error: `Script ${scriptName} not found` });
                return;
            }

            const process = spawn('python', [scriptPath], {
                stdio: this.options.verbose ? 'inherit' : 'pipe'
            });

            let output = '';
            let error = '';

            if (!this.options.verbose) {
                process.stdout?.on('data', (data) => {
                    output += data.toString();
                });

                process.stderr?.on('data', (data) => {
                    error += data.toString();
                });
            }

            process.on('close', (code) => {
                resolve({
                    success: code === 0,
                    output,
                    error: code !== 0 ? error : null
                });
            });

            process.on('error', (err) => {
                resolve({
                    success: false,
                    error: err.message
                });
            });
        });
    }

    async generateSummaryReport() {
        console.log('📄 Step 5: Generating monitoring summary report...');
        
        const reportDir = 'quality-reports';
        if (!fs.existsSync(reportDir)) {
            fs.mkdirSync(reportDir, { recursive: true });
        }

        const duration = this.results.endTime ? 
            (this.results.endTime - this.results.startTime) / 1000 : 
            (Date.now() - this.results.startTime) / 1000;

        const summary = {
            timestamp: new Date().toISOString(),
            pipeline: {
                duration: `${duration.toFixed(2)}s`,
                steps: {
                    validation: this.results.validation,
                    metrics: this.results.metrics,
                    dashboard: this.results.dashboard,
                    alerts: this.results.alerts
                }
            },
            overall: {
                success: this.isOverallSuccess(),
                qualityScore: this.results.metrics?.qualityScore || 0,
                coverage: this.results.metrics?.coverage || 0,
                totalErrors: this.results.metrics?.totalErrors || 0,
                alertsCount: this.results.metrics?.alertsCount || 0
            },
            recommendations: this.generateRecommendations()
        };

        const summaryFile = path.join(reportDir, `monitoring-summary-${Date.now()}.json`);
        fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2));

        // Generate markdown summary
        const markdownSummary = this.generateMarkdownSummary(summary);
        const mdFile = path.join(reportDir, `monitoring-summary-${Date.now()}.md`);
        fs.writeFileSync(mdFile, markdownSummary);

        console.log(`📄 Summary reports generated: ${summaryFile}, ${mdFile}`);
    }

    generateMarkdownSummary(summary) {
        const { pipeline, overall } = summary;
        
        return `# Quality Monitoring Pipeline Summary

**Generated:** ${new Date(summary.timestamp).toLocaleString()}  
**Duration:** ${pipeline.duration}

## 🎯 Overall Results

| Metric | Value | Status |
|--------|-------|--------|
| Pipeline Success | ${overall.success ? 'Yes' : 'No'} | ${overall.success ? '✅' : '❌'} |
| Quality Score | ${overall.qualityScore}/100 | ${this.getScoreStatus(overall.qualityScore, 80)} |
| Test Coverage | ${overall.coverage.toFixed(1)}% | ${this.getScoreStatus(overall.coverage, 80)} |
| Total Errors | ${overall.totalErrors} | ${overall.totalErrors === 0 ? '✅' : '❌'} |
| Active Alerts | ${overall.alertsCount} | ${overall.alertsCount === 0 ? '✅' : '⚠️'} |

## 📋 Pipeline Steps

### 1. Configuration Validation
- **Status:** ${pipeline.steps.validation?.passed ? '✅ Passed' : '❌ Failed'}
- **Timestamp:** ${pipeline.steps.validation?.timestamp || 'N/A'}

### 2. Metrics Collection
- **Status:** ${pipeline.steps.metrics?.success ? '✅ Success' : '❌ Failed'}
- **Quality Score:** ${pipeline.steps.metrics?.qualityScore || 'N/A'}/100
- **Coverage:** ${pipeline.steps.metrics?.coverage?.toFixed(1) || 'N/A'}%
- **Timestamp:** ${pipeline.steps.metrics?.timestamp || 'N/A'}

### 3. Dashboard Generation
- **Status:** ${pipeline.steps.dashboard?.success ? '✅ Success' : '❌ Failed'}
- **Timestamp:** ${pipeline.steps.dashboard?.timestamp || 'N/A'}

### 4. Alerts Monitoring
- **Status:** ${pipeline.steps.alerts?.success ? '✅ Success' : '❌ Failed'}
- **Timestamp:** ${pipeline.steps.alerts?.timestamp || 'N/A'}

## 💡 Recommendations

${summary.recommendations.length > 0 ? 
    summary.recommendations.map((rec, i) => `${i + 1}. ${rec}`).join('\n') : 
    'No specific recommendations at this time.'}

## 🔗 Generated Reports

Check the \`quality-reports/\` directory for detailed reports:
- Quality metrics JSON reports
- Interactive HTML dashboard
- Alert notifications
- Trend analysis data

---
*Generated by AI Scholar Quality Monitoring Pipeline*
`;
    }

    generateRecommendations() {
        const recommendations = [];
        
        if (!this.results.validation?.passed) {
            recommendations.push('Fix configuration validation errors to ensure proper monitoring');
        }
        
        if (!this.results.metrics?.success) {
            recommendations.push('Investigate metrics collection issues to ensure accurate monitoring');
        }
        
        if (this.results.metrics?.qualityScore < 80) {
            recommendations.push('Focus on improving overall quality score through error reduction and coverage improvement');
        }
        
        if (this.results.metrics?.totalErrors > 0) {
            recommendations.push('Address all quality errors (linting, type checking, compilation issues)');
        }
        
        if (this.results.metrics?.coverage < 80) {
            recommendations.push('Increase test coverage by adding unit tests and integration tests');
        }
        
        if (this.results.metrics?.alertsCount > 5) {
            recommendations.push('Address quality alerts to prevent accumulation of technical debt');
        }
        
        if (!this.results.dashboard?.success) {
            recommendations.push('Fix dashboard generation issues to enable visual quality monitoring');
        }
        
        if (!this.results.alerts?.success) {
            recommendations.push('Fix alerts system to ensure timely notification of quality issues');
        }
        
        return recommendations;
    }

    isOverallSuccess() {
        return (
            (this.results.validation?.passed !== false) &&
            (this.results.metrics?.success !== false) &&
            (this.results.dashboard?.success !== false) &&
            (this.results.alerts?.success !== false)
        );
    }

    getScoreStatus(score, threshold) {
        return score >= threshold ? '✅ Good' : score >= threshold * 0.8 ? '⚠️ Fair' : '❌ Poor';
    }

    displayFinalResults() {
        const duration = (this.results.endTime - this.results.startTime) / 1000;
        
        console.log('\n' + '='.repeat(60));
        console.log('🎯 QUALITY MONITORING PIPELINE RESULTS');
        console.log('='.repeat(60));
        console.log(`⏱️ Duration: ${duration.toFixed(2)}s`);
        console.log(`🎯 Overall Success: ${this.isOverallSuccess() ? '✅ Yes' : '❌ No'}`);
        
        if (this.results.metrics) {
            console.log(`📊 Quality Score: ${this.results.metrics.qualityScore || 0}/100`);
            console.log(`🧪 Coverage: ${this.results.metrics.coverage?.toFixed(1) || 0}%`);
            console.log(`🐛 Errors: ${this.results.metrics.totalErrors || 0}`);
            console.log(`🚨 Alerts: ${this.results.metrics.alertsCount || 0}`);
        }
        
        console.log('\n📁 Reports available in quality-reports/ directory');
        console.log('🌐 Open quality-reports/quality-dashboard.html in browser for interactive view');
        console.log('='.repeat(60));
    }
}

// CLI argument parsing
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {};
    
    args.forEach(arg => {
        switch (arg) {
            case '--skip-validation':
                options.skipValidation = true;
                break;
            case '--skip-metrics':
                options.skipMetrics = true;
                break;
            case '--skip-dashboard':
                options.skipDashboard = true;
                break;
            case '--skip-alerts':
                options.skipAlerts = true;
                break;
            case '--verbose':
            case '-v':
                options.verbose = true;
                break;
            case '--help':
            case '-h':
                console.log(`
Quality Monitor - Comprehensive Quality Monitoring Pipeline

Usage: node quality-monitor.js [options]

Options:
  --skip-validation    Skip configuration validation
  --skip-metrics      Skip metrics collection
  --skip-dashboard    Skip dashboard generation
  --skip-alerts       Skip alerts monitoring
  --verbose, -v       Enable verbose output
  --help, -h          Show this help message

Examples:
  node quality-monitor.js                    # Run complete pipeline
  node quality-monitor.js --verbose          # Run with verbose output
  node quality-monitor.js --skip-validation  # Skip config validation
`);
                process.exit(0);
                break;
        }
    });
    
    return options;
}

// Main execution
async function main() {
    try {
        const options = parseArgs();
        const monitor = new QualityMonitor(options);
        const success = await monitor.runCompleteMonitoring();
        
        process.exit(success ? 0 : 1);
    } catch (error) {
        console.error('❌ Quality monitoring failed:', error.message);
        process.exit(1);
    }
}

// Run if called directly
if (process.argv[1] && process.argv[1].endsWith('quality-monitor.js')) {
    main();
}

export { QualityMonitor };
