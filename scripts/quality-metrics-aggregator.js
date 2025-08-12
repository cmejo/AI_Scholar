#!/usr/bin/env node

/**
 * AI Scholar RAG Chatbot - Quality Metrics Aggregator
 * 
 * This script aggregates quality metrics from multiple sources and provides
 * comprehensive analysis, trend detection, and threshold monitoring.
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Import existing quality metrics collector
import { CONFIG, QualityMetricsCollector } from './quality-metrics.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class QualityMetricsAggregator extends QualityMetricsCollector {
    constructor() {
        super();
        this.configFile = 'quality-config.json';
        this.loadConfiguration();
    }

    loadConfiguration() {
        try {
            if (fs.existsSync(this.configFile)) {
                const configData = JSON.parse(fs.readFileSync(this.configFile, 'utf8'));
                Object.assign(CONFIG, configData);
                this.log('✅ Configuration loaded from quality-config.json', 'green');
            }
        } catch (error) {
            this.log(`⚠️ Error loading configuration: ${error.message}`, 'yellow');
        }
    }

    async collectComprehensiveMetrics() {
        this.log('🔍 Starting comprehensive quality metrics aggregation...', 'cyan');
        
        try {
            // Collect base metrics
            await this.collectAllMetrics();
            
            // Collect additional metrics
            await this.collectTechnicalDebtMetrics();
            await this.collectPerformanceMetrics();
            await this.collectDependencyMetrics();
            await this.analyzeCodeQualityTrends();
            await this.generateQualityInsights();
            
            this.log('✅ Comprehensive quality metrics collection completed!', 'green');
            return this.metrics;
        } catch (error) {
            this.log(`❌ Error in comprehensive metrics collection: ${error.message}`, 'red');
            throw error;
        }
    }

    async collectTechnicalDebtMetrics() {
        this.log('💳 Collecting technical debt metrics...', 'blue');
        
        const technicalDebt = {
            todoComments: 0,
            fixmeComments: 0,
            hackComments: 0,
            deprecatedUsage: 0,
            longFunctions: 0,
            complexFunctions: 0,
            duplicateCode: 0,
            estimatedHours: 0
        };

        // Analyze frontend files
        if (fs.existsSync('src')) {
            technicalDebt.frontend = this.analyzeTechnicalDebt('src');
        }

        // Analyze backend files
        if (fs.existsSync('backend')) {
            technicalDebt.backend = this.analyzeTechnicalDebt('backend');
        }

        // Calculate overall technical debt
        technicalDebt.totalItems = (technicalDebt.frontend?.totalItems || 0) + 
                                  (technicalDebt.backend?.totalItems || 0);
        technicalDebt.estimatedHours = technicalDebt.totalItems * 2; // 2 hours per item estimate
        technicalDebt.debtRatio = technicalDebt.totalItems / Math.max(1, this.getTotalFunctions());

        this.metrics.technicalDebt = technicalDebt;
        this.log('✅ Technical debt metrics collected', 'green');
    }

    analyzeTechnicalDebt(directory) {
        const debt = {
            todoComments: 0,
            fixmeComments: 0,
            hackComments: 0,
            deprecatedUsage: 0,
            longFunctions: 0,
            complexFunctions: 0,
            totalItems: 0
        };

        const analyzeFile = (filePath) => {
            try {
                const content = fs.readFileSync(filePath, 'utf8');
                const lines = content.split('\n');

                // Count debt indicators
                debt.todoComments += (content.match(/\/\/.*TODO|#.*TODO/gi) || []).length;
                debt.fixmeComments += (content.match(/\/\/.*FIXME|#.*FIXME/gi) || []).length;
                debt.hackComments += (content.match(/\/\/.*HACK|#.*HACK/gi) || []).length;
                debt.deprecatedUsage += (content.match(/@deprecated|warnings\.warn/gi) || []).length;

                // Analyze function complexity (simplified)
                const functionMatches = content.match(/function\s+\w+|def\s+\w+|const\s+\w+\s*=/g) || [];
                functionMatches.forEach(() => {
                    // Simple heuristic for long/complex functions
                    const complexityIndicators = (content.match(/if|for|while|switch|catch|\?\s*:/g) || []).length;
                    if (lines.length > 50) debt.longFunctions++;
                    if (complexityIndicators > 10) debt.complexFunctions++;
                });

            } catch (error) {
                // Skip files that can't be read
            }
        };

        const walkDirectory = (dir) => {
            if (!fs.existsSync(dir)) return;

            const files = fs.readdirSync(dir);
            files.forEach(file => {
                const filePath = path.join(dir, file);
                const stat = fs.statSync(filePath);

                if (stat.isDirectory() && !file.startsWith('.') && file !== 'node_modules') {
                    walkDirectory(filePath);
                } else if (file.match(/\.(ts|tsx|js|jsx|py)$/)) {
                    analyzeFile(filePath);
                }
            });
        };

        walkDirectory(directory);

        debt.totalItems = debt.todoComments + debt.fixmeComments + debt.hackComments + 
                         debt.longFunctions + debt.complexFunctions;

        return debt;
    }

    async collectPerformanceMetrics() {
        this.log('⚡ Collecting performance metrics...', 'blue');
        
        const performance = {
            buildTime: 0,
            testTime: 0,
            bundleAnalysis: {},
            importTime: 0,
            memoryUsage: 0
        };

        try {
            // Measure build time
            const buildStart = Date.now();
            execSync('npm run build', { stdio: 'pipe' });
            performance.buildTime = (Date.now() - buildStart) / 1000;

            // Measure test time
            const testStart = Date.now();
            execSync('npm run test:run', { stdio: 'pipe' });
            performance.testTime = (Date.now() - testStart) / 1000;

            // Analyze bundle if it exists
            if (fs.existsSync('dist')) {
                performance.bundleAnalysis = this.analyzeBundlePerformance('dist');
            }

        } catch (error) {
            this.log(`⚠️ Performance metrics collection partial: ${error.message}`, 'yellow');
        }

        this.metrics.performance = performance;
        this.log('✅ Performance metrics collected', 'green');
    }

    analyzeBundlePerformance(distDir) {
        const analysis = {
            totalSize: 0,
            jsSize: 0,
            cssSize: 0,
            assetSize: 0,
            chunkCount: 0,
            largestChunk: { name: '', size: 0 }
        };

        const analyzeDir = (dir) => {
            const files = fs.readdirSync(dir);
            
            files.forEach(file => {
                const filePath = path.join(dir, file);
                const stat = fs.statSync(filePath);
                
                if (stat.isDirectory()) {
                    analyzeDir(filePath);
                } else {
                    const size = stat.size;
                    analysis.totalSize += size;
                    
                    if (file.endsWith('.js')) {
                        analysis.jsSize += size;
                        analysis.chunkCount++;
                        if (size > analysis.largestChunk.size) {
                            analysis.largestChunk = { name: file, size };
                        }
                    } else if (file.endsWith('.css')) {
                        analysis.cssSize += size;
                    } else {
                        analysis.assetSize += size;
                    }
                }
            });
        };

        analyzeDir(distDir);
        return analysis;
    }

    async collectDependencyMetrics() {
        this.log('📦 Collecting dependency metrics...', 'blue');
        
        const dependencies = {
            total: 0,
            dev: 0,
            outdated: 0,
            vulnerable: 0,
            licenses: {},
            size: 0
        };

        try {
            // Analyze package.json
            if (fs.existsSync('package.json')) {
                const packageData = JSON.parse(fs.readFileSync('package.json', 'utf8'));
                dependencies.total = Object.keys(packageData.dependencies || {}).length;
                dependencies.dev = Object.keys(packageData.devDependencies || {}).length;
            }

            // Check for outdated packages
            try {
                const outdatedOutput = execSync('npm outdated --json', { encoding: 'utf8', stdio: 'pipe' });
                const outdatedData = JSON.parse(outdatedOutput);
                dependencies.outdated = Object.keys(outdatedData).length;
            } catch (error) {
                // npm outdated returns non-zero exit code when packages are outdated
                dependencies.outdated = 0;
            }

            // Analyze node_modules size
            if (fs.existsSync('node_modules')) {
                dependencies.size = this.getDirectorySize('node_modules');
            }

        } catch (error) {
            this.log(`⚠️ Dependency metrics collection partial: ${error.message}`, 'yellow');
        }

        this.metrics.dependencies = dependencies;
        this.log('✅ Dependency metrics collected', 'green');
    }

    getDirectorySize(dirPath) {
        let totalSize = 0;
        
        const calculateSize = (dir) => {
            try {
                const files = fs.readdirSync(dir);
                files.forEach(file => {
                    const filePath = path.join(dir, file);
                    const stat = fs.statSync(filePath);
                    
                    if (stat.isDirectory()) {
                        calculateSize(filePath);
                    } else {
                        totalSize += stat.size;
                    }
                });
            } catch (error) {
                // Skip directories that can't be read
            }
        };

        calculateSize(dirPath);
        return totalSize;
    }

    getTotalFunctions() {
        // Simplified function count estimation
        let totalFunctions = 0;
        
        const countFunctions = (dir) => {
            if (!fs.existsSync(dir)) return;
            
            const files = fs.readdirSync(dir);
            files.forEach(file => {
                const filePath = path.join(dir, file);
                const stat = fs.statSync(filePath);
                
                if (stat.isDirectory() && !file.startsWith('.') && file !== 'node_modules') {
                    countFunctions(filePath);
                } else if (file.match(/\.(ts|tsx|js|jsx|py)$/)) {
                    try {
                        const content = fs.readFileSync(filePath, 'utf8');
                        const functionMatches = content.match(/function\s+\w+|def\s+\w+|const\s+\w+\s*=/g) || [];
                        totalFunctions += functionMatches.length;
                    } catch (error) {
                        // Skip files that can't be read
                    }
                }
            });
        };

        countFunctions('src');
        countFunctions('backend');
        
        return totalFunctions;
    }

    async analyzeCodeQualityTrends() {
        this.log('📈 Analyzing code quality trends...', 'blue');
        
        const trendsFile = path.join(CONFIG.outputDir, 'quality-trends-detailed.json');
        let trends = [];
        
        if (fs.existsSync(trendsFile)) {
            try {
                trends = JSON.parse(fs.readFileSync(trendsFile, 'utf8'));
            } catch (error) {
                this.log('⚠️ Could not read trends data', 'yellow');
            }
        }

        if (trends.length >= 2) {
            const trendAnalysis = this.calculateTrendAnalysis(trends);
            this.metrics.trendAnalysis = trendAnalysis;
            
            // Generate trend-based alerts
            this.generateTrendAlerts(trendAnalysis);
        }

        this.log('✅ Code quality trends analyzed', 'green');
    }

    calculateTrendAnalysis(trends) {
        const recent = trends.slice(-CONFIG.thresholds.trends.trend_analysis_window);
        const analysis = {
            qualityScoreTrend: 'stable',
            coverageTrend: 'stable',
            errorTrend: 'stable',
            securityTrend: 'stable',
            recommendations: []
        };

        if (recent.length >= 3) {
            // Analyze quality score trend
            const qualityScores = recent.map(t => t.overall.qualityScore);
            const qualityTrend = this.calculateTrend(qualityScores);
            analysis.qualityScoreTrend = qualityTrend.direction;
            analysis.qualityScoreChange = qualityTrend.change;

            // Analyze coverage trend
            const coverageValues = recent.map(t => t.overall.coverage);
            const coverageTrend = this.calculateTrend(coverageValues);
            analysis.coverageTrend = coverageTrend.direction;
            analysis.coverageChange = coverageTrend.change;

            // Analyze error trend
            const errorValues = recent.map(t => t.overall.totalErrors);
            const errorTrend = this.calculateTrend(errorValues);
            analysis.errorTrend = errorTrend.direction;
            analysis.errorChange = errorTrend.change;
        }

        return analysis;
    }

    calculateTrend(values) {
        if (values.length < 2) return { direction: 'stable', change: 0 };

        const first = values[0];
        const last = values[values.length - 1];
        const change = last - first;
        const percentChange = Math.abs(change / Math.max(first, 1)) * 100;

        let direction = 'stable';
        if (percentChange > 5) {
            direction = change > 0 ? 'increasing' : 'decreasing';
        }

        return { direction, change, percentChange };
    }

    generateTrendAlerts(trendAnalysis) {
        const thresholds = CONFIG.thresholds.trends;

        // Quality score declining
        if (trendAnalysis.qualityScoreTrend === 'decreasing' && 
            Math.abs(trendAnalysis.qualityScoreChange) > thresholds.max_quality_decline) {
            this.metrics.alerts.push({
                type: 'quality_trend',
                severity: 'warning',
                message: `Quality score declining by ${Math.abs(trendAnalysis.qualityScoreChange).toFixed(1)} points`,
                recommendation: 'Investigate recent changes that may have impacted code quality'
            });
        }

        // Coverage declining
        if (trendAnalysis.coverageTrend === 'decreasing' && 
            Math.abs(trendAnalysis.coverageChange) > thresholds.max_coverage_decline) {
            this.metrics.alerts.push({
                type: 'coverage_trend',
                severity: 'warning',
                message: `Test coverage declining by ${Math.abs(trendAnalysis.coverageChange).toFixed(1)}%`,
                recommendation: 'Add tests for new code and maintain coverage standards'
            });
        }

        // Errors increasing
        if (trendAnalysis.errorTrend === 'increasing' && 
            trendAnalysis.errorChange > thresholds.max_error_increase) {
            this.metrics.alerts.push({
                type: 'error_trend',
                severity: 'warning',
                message: `Error count increasing by ${trendAnalysis.errorChange}`,
                recommendation: 'Address the root cause of increasing errors'
            });
        }
    }

    async generateQualityInsights() {
        this.log('🧠 Generating quality insights...', 'blue');
        
        const insights = {
            strengths: [],
            weaknesses: [],
            recommendations: [],
            riskAreas: []
        };

        const { overall, frontend, backend, technicalDebt, performance } = this.metrics;

        // Identify strengths
        if (overall.qualityScore >= 90) insights.strengths.push('Excellent overall quality score');
        if (overall.coverage >= 90) insights.strengths.push('High test coverage');
        if (overall.totalErrors === 0) insights.strengths.push('No quality errors detected');
        if (overall.securityScore >= 95) insights.strengths.push('Strong security posture');

        // Identify weaknesses
        if (overall.qualityScore < 70) insights.weaknesses.push('Low overall quality score');
        if (overall.coverage < 60) insights.weaknesses.push('Insufficient test coverage');
        if (overall.totalErrors > 10) insights.weaknesses.push('High number of quality errors');
        if (technicalDebt?.totalItems > 50) insights.weaknesses.push('High technical debt');

        // Generate recommendations
        if (frontend.bundle?.totalSize > 3000000) {
            insights.recommendations.push('Consider implementing code splitting to reduce bundle size');
        }
        if (performance?.buildTime > 120) {
            insights.recommendations.push('Optimize build process to reduce build time');
        }
        if (technicalDebt?.debtRatio > 0.2) {
            insights.recommendations.push('Prioritize technical debt reduction');
        }

        // Identify risk areas
        if (backend.security?.highSeverity > 0) {
            insights.riskAreas.push('High-severity security vulnerabilities');
        }
        if (overall.maintainabilityIndex < 50) {
            insights.riskAreas.push('Low maintainability index');
        }

        this.metrics.insights = insights;
        this.log('✅ Quality insights generated', 'green');
    }

    async generateEnhancedReports() {
        this.log('📄 Generating enhanced quality reports...', 'blue');
        
        // Generate comprehensive JSON report
        const jsonReport = path.join(CONFIG.outputDir, `comprehensive-quality-report-${Date.now()}.json`);
        fs.writeFileSync(jsonReport, JSON.stringify(this.metrics, null, 2));
        
        // Generate executive summary
        const executiveSummary = this.generateExecutiveSummary();
        const summaryFile = path.join(CONFIG.outputDir, `quality-executive-summary-${Date.now()}.md`);
        fs.writeFileSync(summaryFile, executiveSummary);
        
        // Generate detailed technical report
        const technicalReport = this.generateTechnicalReport();
        const techFile = path.join(CONFIG.outputDir, `quality-technical-report-${Date.now()}.md`);
        fs.writeFileSync(techFile, technicalReport);
        
        this.log(`📄 Enhanced reports generated: ${jsonReport}, ${summaryFile}, ${techFile}`, 'green');
    }

    generateExecutiveSummary() {
        const { overall, insights, alerts, timestamp } = this.metrics;
        
        return `# Quality Executive Summary

**Generated:** ${new Date(timestamp).toLocaleString()}

## 🎯 Key Metrics

| Metric | Score | Status |
|--------|-------|--------|
| Overall Quality | ${overall.qualityScore}/100 | ${this.getScoreStatus(overall.qualityScore, 80)} |
| Test Coverage | ${overall.coverage.toFixed(1)}% | ${this.getScoreStatus(overall.coverage, 80)} |
| Security Score | ${overall.securityScore}/100 | ${this.getScoreStatus(overall.securityScore, 90)} |
| Maintainability | ${overall.maintainabilityIndex}/100 | ${this.getScoreStatus(overall.maintainabilityIndex, 70)} |

## 📊 Quality Status

**Overall Assessment:** ${this.getOverallAssessment()}

**Active Alerts:** ${alerts.length}

## 💪 Strengths

${insights.strengths.length > 0 ? insights.strengths.map(s => `- ${s}`).join('\n') : '- No specific strengths identified'}

## ⚠️ Areas for Improvement

${insights.weaknesses.length > 0 ? insights.weaknesses.map(w => `- ${w}`).join('\n') : '- No major weaknesses identified'}

## 🎯 Top Recommendations

${insights.recommendations.slice(0, 5).map((r, i) => `${i + 1}. ${r}`).join('\n')}

## 🚨 Risk Areas

${insights.riskAreas.length > 0 ? insights.riskAreas.map(r => `- ${r}`).join('\n') : '- No significant risk areas identified'}

---
*This executive summary provides a high-level overview of code quality metrics.*
`;
    }

    generateTechnicalReport() {
        const { frontend, backend, technicalDebt, performance, dependencies } = this.metrics;
        
        return `# Technical Quality Report

## 🎨 Frontend Analysis

### Code Quality
- **ESLint Errors:** ${frontend.eslint?.errorCount || 0}
- **ESLint Warnings:** ${frontend.eslint?.warningCount || 0}
- **TypeScript Errors:** ${frontend.typescript?.errors || 0}

### Test Coverage
- **Statements:** ${frontend.coverage?.statements || 0}%
- **Branches:** ${frontend.coverage?.branches || 0}%
- **Functions:** ${frontend.coverage?.functions || 0}%
- **Lines:** ${frontend.coverage?.lines || 0}%

### Bundle Analysis
- **Total Size:** ${frontend.bundle?.totalSizeFormatted || 'N/A'}
- **JS Size:** ${this.formatBytes(performance?.bundleAnalysis?.jsSize || 0)}
- **CSS Size:** ${this.formatBytes(performance?.bundleAnalysis?.cssSize || 0)}
- **Chunk Count:** ${performance?.bundleAnalysis?.chunkCount || 0}

## 🐍 Backend Analysis

### Code Quality
- **Flake8 Issues:** ${backend.flake8?.totalIssues || 0}
- **MyPy Errors:** ${backend.mypy?.errors || 0}
- **Type Check Status:** ${backend.mypy?.typeCheckSuccess ? 'Pass' : 'Fail'}

### Security Analysis
- **Total Issues:** ${backend.security?.totalIssues || 0}
- **High Severity:** ${backend.security?.highSeverity || 0}
- **Medium Severity:** ${backend.security?.mediumSeverity || 0}
- **Low Severity:** ${backend.security?.lowSeverity || 0}

### Dependencies
- **Vulnerabilities:** ${backend.dependencies?.vulnerabilities || 0}
- **Security Score:** ${backend.dependencies?.securityScore || 100}/100

## 💳 Technical Debt Analysis

### Overall Debt
- **Total Items:** ${technicalDebt?.totalItems || 0}
- **Estimated Hours:** ${technicalDebt?.estimatedHours || 0}
- **Debt Ratio:** ${(technicalDebt?.debtRatio || 0).toFixed(3)}

### Debt Breakdown
- **TODO Comments:** ${technicalDebt?.frontend?.todoComments || 0} (Frontend) + ${technicalDebt?.backend?.todoComments || 0} (Backend)
- **FIXME Comments:** ${technicalDebt?.frontend?.fixmeComments || 0} (Frontend) + ${technicalDebt?.backend?.fixmeComments || 0} (Backend)
- **Long Functions:** ${technicalDebt?.frontend?.longFunctions || 0} (Frontend) + ${technicalDebt?.backend?.longFunctions || 0} (Backend)
- **Complex Functions:** ${technicalDebt?.frontend?.complexFunctions || 0} (Frontend) + ${technicalDebt?.backend?.complexFunctions || 0} (Backend)

## ⚡ Performance Metrics

- **Build Time:** ${performance?.buildTime || 0}s
- **Test Time:** ${performance?.testTime || 0}s
- **Bundle Size:** ${this.formatBytes(performance?.bundleAnalysis?.totalSize || 0)}
- **Largest Chunk:** ${performance?.bundleAnalysis?.largestChunk?.name || 'N/A'} (${this.formatBytes(performance?.bundleAnalysis?.largestChunk?.size || 0)})

## 📦 Dependency Analysis

- **Total Dependencies:** ${dependencies?.total || 0}
- **Dev Dependencies:** ${dependencies?.dev || 0}
- **Outdated Packages:** ${dependencies?.outdated || 0}
- **Node Modules Size:** ${this.formatBytes(dependencies?.size || 0)}

---
*This technical report provides detailed metrics for development teams.*
`;
    }

    getScoreStatus(score, threshold) {
        return score >= threshold ? '✅ Good' : score >= threshold * 0.8 ? '⚠️ Fair' : '❌ Poor';
    }

    getOverallAssessment() {
        const { overall } = this.metrics;
        
        if (overall.qualityScore >= 90) return '🟢 Excellent';
        if (overall.qualityScore >= 80) return '🟡 Good';
        if (overall.qualityScore >= 70) return '🟠 Fair';
        return '🔴 Needs Improvement';
    }
}

// Main execution
async function main() {
    try {
        const aggregator = new QualityMetricsAggregator();
        await aggregator.collectComprehensiveMetrics();
        await aggregator.generateEnhancedReports();
        
        console.log('\n🎉 Comprehensive quality metrics collection completed successfully!');
        console.log(`📊 View reports in the ${CONFIG.outputDir}/ directory`);
        
        process.exit(0);
    } catch (error) {
        console.error('❌ Quality metrics aggregation failed:', error.message);
        process.exit(1);
    }
}

// Run if called directly
if (process.argv[1] && process.argv[1].endsWith('quality-metrics-aggregator.js')) {
    main();
}

export { QualityMetricsAggregator };
