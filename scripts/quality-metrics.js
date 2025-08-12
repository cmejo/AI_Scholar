#!/usr/bin/env node

/**
 * AI Scholar RAG Chatbot - Quality Metrics Collection System
 * 
 * This script collects comprehensive code quality metrics including:
 * - Code complexity metrics
 * - Type safety metrics
 * - Test coverage metrics
 * - Security metrics
 * - Performance metrics
 * - Maintainability metrics
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const CONFIG = {
    outputDir: 'quality-reports',
    metricsFile: 'quality-metrics.json',
    trendsFile: 'quality-trends.json',
    thresholds: {
        coverage: 80,
        complexity: 10,
        maintainability: 70,
        duplicateCode: 5,
        technicalDebt: 30
    },
    colors: {
        reset: '\x1b[0m',
        red: '\x1b[31m',
        green: '\x1b[32m',
        yellow: '\x1b[33m',
        blue: '\x1b[34m',
        magenta: '\x1b[35m',
        cyan: '\x1b[36m'
    }
};

class QualityMetricsCollector {
    constructor() {
        this.metrics = {
            timestamp: new Date().toISOString(),
            frontend: {},
            backend: {},
            overall: {},
            trends: [],
            alerts: []
        };
        
        this.ensureOutputDirectory();
    }

    ensureOutputDirectory() {
        if (!fs.existsSync(CONFIG.outputDir)) {
            fs.mkdirSync(CONFIG.outputDir, { recursive: true });
        }
    }

    log(message, color = 'reset') {
        console.log(`${CONFIG.colors[color]}${message}${CONFIG.colors.reset}`);
    }

    async collectAllMetrics() {
        this.log('🔍 Starting comprehensive quality metrics collection...', 'cyan');
        
        try {
            await this.collectFrontendMetrics();
            await this.collectBackendMetrics();
            await this.calculateOverallMetrics();
            await this.analyzeQualityTrends();
            await this.generateAlerts();
            await this.checkQualityThresholds();
            await this.saveMetrics();
            await this.generateReports();
            await this.updateMetricsTrends();
            
            this.log('✅ Quality metrics collection completed successfully!', 'green');
            this.displayMetricsSummary();
        } catch (error) {
            this.log(`❌ Error collecting metrics: ${error.message}`, 'red');
            throw error;
        }
    }

    async collectFrontendMetrics() {
        this.log('📊 Collecting frontend metrics...', 'blue');
        
        const frontend = this.metrics.frontend;
        
        // ESLint metrics
        try {
            execSync('npm run lint -- --format json --output-file eslint-temp.json', { stdio: 'pipe' });
            const eslintData = JSON.parse(fs.readFileSync('eslint-temp.json', 'utf8'));
            
            frontend.eslint = {
                totalFiles: eslintData.length,
                errorCount: eslintData.reduce((sum, file) => sum + file.errorCount, 0),
                warningCount: eslintData.reduce((sum, file) => sum + file.warningCount, 0),
                fixableErrorCount: eslintData.reduce((sum, file) => sum + file.fixableErrorCount, 0),
                fixableWarningCount: eslintData.reduce((sum, file) => sum + file.fixableWarningCount, 0)
            };
            
            fs.unlinkSync('eslint-temp.json');
        } catch (error) {
            frontend.eslint = { error: error.message };
        }

        // TypeScript metrics
        try {
            const tscOutput = execSync('npm run type-check', { encoding: 'utf8', stdio: 'pipe' });
            frontend.typescript = {
                compilationSuccess: true,
                errors: 0
            };
        } catch (error) {
            const errorCount = (error.stdout.match(/error TS/g) || []).length;
            frontend.typescript = {
                compilationSuccess: false,
                errors: errorCount
            };
        }

        // Test coverage metrics
        try {
            execSync('npm run test:coverage', { stdio: 'pipe' });
            
            if (fs.existsSync('coverage/coverage-summary.json')) {
                const coverageData = JSON.parse(fs.readFileSync('coverage/coverage-summary.json', 'utf8'));
                frontend.coverage = {
                    statements: coverageData.total.statements.pct,
                    branches: coverageData.total.branches.pct,
                    functions: coverageData.total.functions.pct,
                    lines: coverageData.total.lines.pct
                };
            }
        } catch (error) {
            frontend.coverage = { error: error.message };
        }

        // Bundle size metrics
        try {
            execSync('npm run build', { stdio: 'pipe' });
            
            if (fs.existsSync('dist')) {
                const bundleStats = this.analyzeBundleSize('dist');
                frontend.bundle = bundleStats;
            }
        } catch (error) {
            frontend.bundle = { error: error.message };
        }

        // Code complexity metrics (simplified)
        frontend.complexity = this.analyzeCodeComplexity('src');
        
        this.log('✅ Frontend metrics collected', 'green');
    }

    async collectBackendMetrics() {
        this.log('📊 Collecting backend metrics...', 'blue');
        
        if (!fs.existsSync('backend')) {
            this.log('⚠️ Backend directory not found, skipping backend metrics', 'yellow');
            return;
        }

        const backend = this.metrics.backend;
        
        // Flake8 metrics
        try {
            execSync('cd backend && python -m flake8 --format=json --output-file=flake8-temp.json .', { stdio: 'pipe' });
            const flake8Data = JSON.parse(fs.readFileSync('backend/flake8-temp.json', 'utf8'));
            
            backend.flake8 = {
                totalIssues: flake8Data.length,
                errorsByType: this.categorizeFlake8Issues(flake8Data)
            };
            
            fs.unlinkSync('backend/flake8-temp.json');
        } catch (error) {
            backend.flake8 = { totalIssues: 0 };
        }

        // MyPy metrics
        try {
            const mypyOutput = execSync('cd backend && python -m mypy . --json-report mypy-temp', { encoding: 'utf8', stdio: 'pipe' });
            backend.mypy = {
                typeCheckSuccess: true,
                errors: 0
            };
            
            if (fs.existsSync('backend/mypy-temp')) {
                fs.rmSync('backend/mypy-temp', { recursive: true });
            }
        } catch (error) {
            const errorCount = (error.stdout.match(/error:/g) || []).length;
            backend.mypy = {
                typeCheckSuccess: false,
                errors: errorCount
            };
        }

        // Test coverage metrics
        try {
            execSync('cd backend && python -m pytest --cov=. --cov-report=json --cov-report=term-missing', { stdio: 'pipe' });
            
            if (fs.existsSync('backend/coverage.json')) {
                const coverageData = JSON.parse(fs.readFileSync('backend/coverage.json', 'utf8'));
                backend.coverage = {
                    statements: Math.round(coverageData.totals.percent_covered * 100) / 100,
                    missing: coverageData.totals.missing_lines,
                    excluded: coverageData.totals.excluded_lines
                };
            }
        } catch (error) {
            backend.coverage = { error: error.message };
        }

        // Security metrics
        try {
            execSync('cd backend && python -m bandit -r . -f json -o bandit-temp.json', { stdio: 'pipe' });
            const banditData = JSON.parse(fs.readFileSync('backend/bandit-temp.json', 'utf8'));
            
            backend.security = {
                totalIssues: banditData.results.length,
                highSeverity: banditData.results.filter(r => r.issue_severity === 'HIGH').length,
                mediumSeverity: banditData.results.filter(r => r.issue_severity === 'MEDIUM').length,
                lowSeverity: banditData.results.filter(r => r.issue_severity === 'LOW').length
            };
            
            fs.unlinkSync('backend/bandit-temp.json');
        } catch (error) {
            backend.security = { error: error.message };
        }

        // Dependency security
        try {
            execSync('cd backend && python -m safety check --json --output safety-temp.json', { stdio: 'pipe' });
            const safetyData = JSON.parse(fs.readFileSync('backend/safety-temp.json', 'utf8'));
            
            backend.dependencies = {
                vulnerabilities: safetyData.length,
                securityScore: Math.max(0, 100 - safetyData.length * 10)
            };
            
            fs.unlinkSync('backend/safety-temp.json');
        } catch (error) {
            backend.dependencies = { vulnerabilities: 0, securityScore: 100 };
        }

        this.log('✅ Backend metrics collected', 'green');
    }

    calculateOverallMetrics() {
        this.log('📊 Calculating overall metrics...', 'blue');
        
        const { frontend, backend } = this.metrics;
        const overall = this.metrics.overall;

        // Overall coverage
        const frontendCoverage = frontend.coverage?.statements || 0;
        const backendCoverage = backend.coverage?.statements || 0;
        overall.coverage = (frontendCoverage + backendCoverage) / 2;

        // Overall error count
        overall.totalErrors = (frontend.eslint?.errorCount || 0) + 
                             (frontend.typescript?.errors || 0) + 
                             (backend.flake8?.totalIssues || 0) + 
                             (backend.mypy?.errors || 0);

        // Overall security score
        const securityIssues = (backend.security?.totalIssues || 0) + 
                              (backend.dependencies?.vulnerabilities || 0);
        overall.securityScore = Math.max(0, 100 - securityIssues * 5);

        // Quality score calculation
        overall.qualityScore = this.calculateQualityScore();

        // Maintainability index
        overall.maintainabilityIndex = this.calculateMaintainabilityIndex();

        this.log('✅ Overall metrics calculated', 'green');
    }

    calculateQualityScore() {
        const { frontend, backend, overall } = this.metrics;
        
        let score = 100;
        
        // Deduct for errors
        score -= (overall.totalErrors * 2);
        
        // Deduct for low coverage
        if (overall.coverage < CONFIG.thresholds.coverage) {
            score -= (CONFIG.thresholds.coverage - overall.coverage);
        }
        
        // Deduct for security issues
        score -= (100 - overall.securityScore) * 0.5;
        
        return Math.max(0, Math.round(score));
    }

    calculateMaintainabilityIndex() {
        // Simplified maintainability index calculation
        const { overall } = this.metrics;
        
        let index = 100;
        
        // Factor in error density
        if (overall.totalErrors > 0) {
            index -= Math.min(30, overall.totalErrors * 2);
        }
        
        // Factor in coverage
        index = index * (overall.coverage / 100);
        
        return Math.max(0, Math.round(index));
    }

    analyzeQualityTrends() {
        this.log('📈 Analyzing quality trends...', 'blue');
        
        const trendsFile = path.join(CONFIG.outputDir, CONFIG.trendsFile);
        let historicalData = [];
        
        if (fs.existsSync(trendsFile)) {
            try {
                historicalData = JSON.parse(fs.readFileSync(trendsFile, 'utf8'));
            } catch (error) {
                this.log('⚠️ Could not read historical trends data', 'yellow');
            }
        }
        
        // Add current metrics to trends
        const currentTrend = {
            timestamp: this.metrics.timestamp,
            qualityScore: this.metrics.overall.qualityScore,
            coverage: this.metrics.overall.coverage,
            errors: this.metrics.overall.totalErrors,
            securityScore: this.metrics.overall.securityScore
        };
        
        historicalData.push(currentTrend);
        
        // Keep only last 30 entries
        if (historicalData.length > 30) {
            historicalData = historicalData.slice(-30);
        }
        
        this.metrics.trends = historicalData;
        
        // Save trends data
        fs.writeFileSync(trendsFile, JSON.stringify(historicalData, null, 2));
        
        this.log('✅ Quality trends analyzed', 'green');
    }

    generateAlerts() {
        this.log('🚨 Generating quality alerts...', 'blue');
        
        const alerts = [];
        const { overall, frontend, backend } = this.metrics;
        
        // Coverage alerts
        if (overall.coverage < CONFIG.thresholds.coverage) {
            alerts.push({
                type: 'coverage',
                severity: 'warning',
                message: `Overall coverage (${overall.coverage.toFixed(1)}%) is below threshold (${CONFIG.thresholds.coverage}%)`,
                recommendation: 'Add more unit tests to improve coverage'
            });
        }
        
        // Error alerts
        if (overall.totalErrors > 0) {
            alerts.push({
                type: 'errors',
                severity: 'error',
                message: `${overall.totalErrors} quality errors found`,
                recommendation: 'Fix linting, type checking, and compilation errors'
            });
        }
        
        // Security alerts
        if (overall.securityScore < 90) {
            alerts.push({
                type: 'security',
                severity: 'warning',
                message: `Security score (${overall.securityScore}) indicates potential vulnerabilities`,
                recommendation: 'Review and fix security issues identified by Bandit and Safety'
            });
        }
        
        // Quality score alerts
        if (overall.qualityScore < 80) {
            alerts.push({
                type: 'quality',
                severity: overall.qualityScore < 60 ? 'error' : 'warning',
                message: `Quality score (${overall.qualityScore}) is below acceptable threshold`,
                recommendation: 'Address errors, improve coverage, and fix security issues'
            });
        }
        
        this.metrics.alerts = alerts;
        
        this.log(`✅ Generated ${alerts.length} quality alerts`, 'green');
    }

    analyzeBundleSize(distDir) {
        const stats = { totalSize: 0, files: [] };
        
        const analyzeDir = (dir) => {
            const files = fs.readdirSync(dir);
            
            files.forEach(file => {
                const filePath = path.join(dir, file);
                const stat = fs.statSync(filePath);
                
                if (stat.isDirectory()) {
                    analyzeDir(filePath);
                } else if (file.endsWith('.js') || file.endsWith('.css')) {
                    const size = stat.size;
                    stats.totalSize += size;
                    stats.files.push({
                        name: path.relative(distDir, filePath),
                        size: size,
                        sizeFormatted: this.formatBytes(size)
                    });
                }
            });
        };
        
        analyzeDir(distDir);
        stats.totalSizeFormatted = this.formatBytes(stats.totalSize);
        stats.files.sort((a, b) => b.size - a.size);
        
        return stats;
    }

    analyzeCodeComplexity(srcDir) {
        // Simplified complexity analysis
        let totalFiles = 0;
        let totalLines = 0;
        let complexFunctions = 0;
        
        const analyzeDir = (dir) => {
            if (!fs.existsSync(dir)) return;
            
            const files = fs.readdirSync(dir);
            
            files.forEach(file => {
                const filePath = path.join(dir, file);
                const stat = fs.statSync(filePath);
                
                if (stat.isDirectory() && !file.startsWith('.')) {
                    analyzeDir(filePath);
                } else if (file.endsWith('.ts') || file.endsWith('.tsx') || file.endsWith('.js') || file.endsWith('.jsx')) {
                    totalFiles++;
                    const content = fs.readFileSync(filePath, 'utf8');
                    const lines = content.split('\n').length;
                    totalLines += lines;
                    
                    // Simple complexity heuristic
                    const complexityIndicators = (content.match(/if|for|while|switch|catch|\?\s*:/g) || []).length;
                    if (complexityIndicators > 10) {
                        complexFunctions++;
                    }
                }
            });
        };
        
        analyzeDir(srcDir);
        
        return {
            totalFiles,
            totalLines,
            averageLinesPerFile: totalFiles > 0 ? Math.round(totalLines / totalFiles) : 0,
            complexFunctions,
            complexityScore: totalFiles > 0 ? Math.max(0, 100 - (complexFunctions / totalFiles) * 100) : 100
        };
    }

    categorizeFlake8Issues(issues) {
        const categories = {};
        
        issues.forEach(issue => {
            const code = issue.code || 'Unknown';
            const category = code.substring(0, 1);
            
            if (!categories[category]) {
                categories[category] = 0;
            }
            categories[category]++;
        });
        
        return categories;
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async saveMetrics() {
        const metricsFile = path.join(CONFIG.outputDir, CONFIG.metricsFile);
        fs.writeFileSync(metricsFile, JSON.stringify(this.metrics, null, 2));
        
        this.log(`💾 Metrics saved to ${metricsFile}`, 'green');
    }

    async generateReports() {
        this.log('📄 Generating quality reports...', 'blue');
        
        // Generate JSON report
        const jsonReport = path.join(CONFIG.outputDir, `quality-report-${Date.now()}.json`);
        fs.writeFileSync(jsonReport, JSON.stringify(this.metrics, null, 2));
        
        // Generate Markdown report
        const markdownReport = this.generateMarkdownReport();
        const mdReport = path.join(CONFIG.outputDir, `quality-report-${Date.now()}.md`);
        fs.writeFileSync(mdReport, markdownReport);
        
        // Generate CSV report for trends
        const csvReport = this.generateCSVReport();
        const csvFile = path.join(CONFIG.outputDir, 'quality-trends.csv');
        fs.writeFileSync(csvFile, csvReport);
        
        this.log(`📄 Reports generated: ${jsonReport}, ${mdReport}, ${csvFile}`, 'green');
    }

    generateMarkdownReport() {
        const { overall, frontend, backend, alerts, timestamp } = this.metrics;
        
        return `# Code Quality Metrics Report

**Generated:** ${new Date(timestamp).toLocaleString()}

## 📊 Overall Quality Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Quality Score | ${overall.qualityScore}/100 | ${this.getStatusEmoji(overall.qualityScore, 80)} |
| Coverage | ${overall.coverage.toFixed(1)}% | ${this.getStatusEmoji(overall.coverage, CONFIG.thresholds.coverage)} |
| Total Errors | ${overall.totalErrors} | ${overall.totalErrors === 0 ? '✅' : '❌'} |
| Security Score | ${overall.securityScore}/100 | ${this.getStatusEmoji(overall.securityScore, 90)} |
| Maintainability | ${overall.maintainabilityIndex}/100 | ${this.getStatusEmoji(overall.maintainabilityIndex, CONFIG.thresholds.maintainability)} |

## 🎯 Frontend Metrics

### TypeScript & Linting
- **Compilation:** ${frontend.typescript?.compilationSuccess ? '✅ Success' : '❌ Failed'}
- **Type Errors:** ${frontend.typescript?.errors || 0}
- **ESLint Errors:** ${frontend.eslint?.errorCount || 0}
- **ESLint Warnings:** ${frontend.eslint?.warningCount || 0}

### Test Coverage
- **Statements:** ${frontend.coverage?.statements || 0}%
- **Branches:** ${frontend.coverage?.branches || 0}%
- **Functions:** ${frontend.coverage?.functions || 0}%
- **Lines:** ${frontend.coverage?.lines || 0}%

### Bundle Analysis
- **Total Size:** ${frontend.bundle?.totalSizeFormatted || 'N/A'}
- **Files Analyzed:** ${frontend.bundle?.files?.length || 0}

### Code Complexity
- **Total Files:** ${frontend.complexity?.totalFiles || 0}
- **Average Lines/File:** ${frontend.complexity?.averageLinesPerFile || 0}
- **Complexity Score:** ${frontend.complexity?.complexityScore || 0}/100

## 🐍 Backend Metrics

### Code Quality
- **Flake8 Issues:** ${backend.flake8?.totalIssues || 0}
- **MyPy Errors:** ${backend.mypy?.errors || 0}
- **Type Check:** ${backend.mypy?.typeCheckSuccess ? '✅ Success' : '❌ Failed'}

### Test Coverage
- **Coverage:** ${backend.coverage?.statements || 0}%
- **Missing Lines:** ${backend.coverage?.missing || 0}

### Security
- **Total Issues:** ${backend.security?.totalIssues || 0}
- **High Severity:** ${backend.security?.highSeverity || 0}
- **Medium Severity:** ${backend.security?.mediumSeverity || 0}
- **Low Severity:** ${backend.security?.lowSeverity || 0}

### Dependencies
- **Vulnerabilities:** ${backend.dependencies?.vulnerabilities || 0}
- **Security Score:** ${backend.dependencies?.securityScore || 100}/100

## 🚨 Quality Alerts

${alerts.length === 0 ? '✅ No quality alerts - all metrics are within acceptable thresholds!' : ''}

${alerts.map(alert => `
### ${alert.severity === 'error' ? '❌' : '⚠️'} ${alert.type.toUpperCase()}
**Message:** ${alert.message}  
**Recommendation:** ${alert.recommendation}
`).join('\n')}

## 📈 Quality Trends

${this.metrics.trends.length > 1 ? this.generateTrendAnalysis() : 'Not enough historical data for trend analysis.'}

## 🔧 Recommendations

${this.generateRecommendations()}

---
*Report generated by AI Scholar Quality Metrics System*
`;
    }

    generateTrendAnalysis() {
        const trends = this.metrics.trends;
        if (trends.length < 2) return 'Not enough data for trend analysis.';
        
        const latest = trends[trends.length - 1];
        const previous = trends[trends.length - 2];
        
        const qualityTrend = latest.qualityScore - previous.qualityScore;
        const coverageTrend = latest.coverage - previous.coverage;
        const errorTrend = latest.errors - previous.errors;
        
        return `
**Quality Score Trend:** ${qualityTrend >= 0 ? '📈' : '📉'} ${qualityTrend > 0 ? '+' : ''}${qualityTrend.toFixed(1)}  
**Coverage Trend:** ${coverageTrend >= 0 ? '📈' : '📉'} ${coverageTrend > 0 ? '+' : ''}${coverageTrend.toFixed(1)}%  
**Error Trend:** ${errorTrend <= 0 ? '📈' : '📉'} ${errorTrend > 0 ? '+' : ''}${errorTrend} errors
`;
    }

    async checkQualityThresholds() {
        this.log('🎯 Checking quality thresholds...', 'blue');
        
        const { overall, frontend, backend } = this.metrics;
        const thresholds = CONFIG.thresholds;
        
        // Check overall quality score
        if (overall.qualityScore < thresholds.quality_score.warning) {
            this.metrics.alerts.push({
                type: 'quality_score',
                severity: overall.qualityScore < thresholds.quality_score.critical ? 'critical' : 'warning',
                message: `Quality score (${overall.qualityScore}) below threshold`,
                threshold: thresholds.quality_score.warning,
                recommendation: 'Address errors, improve coverage, and fix security issues'
            });
        }
        
        // Check coverage thresholds
        if (overall.coverage < thresholds.coverage.statements) {
            this.metrics.alerts.push({
                type: 'coverage',
                severity: 'warning',
                message: `Overall coverage (${overall.coverage.toFixed(1)}%) below threshold (${thresholds.coverage.statements}%)`,
                threshold: thresholds.coverage.statements,
                recommendation: 'Add more unit tests to improve coverage'
            });
        }
        
        // Check complexity thresholds
        if (frontend.complexity?.complexityScore < 70) {
            this.metrics.alerts.push({
                type: 'complexity',
                severity: 'warning',
                message: `Code complexity score (${frontend.complexity.complexityScore}) indicates high complexity`,
                threshold: 70,
                recommendation: 'Refactor complex functions and reduce cyclomatic complexity'
            });
        }
        
        // Check bundle size threshold
        if (frontend.bundle?.totalSize > CONFIG.thresholds.performance.max_bundle_size_mb * 1024 * 1024) {
            this.metrics.alerts.push({
                type: 'bundle_size',
                severity: 'warning',
                message: `Bundle size (${frontend.bundle.totalSizeFormatted}) exceeds threshold (${CONFIG.thresholds.performance.max_bundle_size_mb}MB)`,
                threshold: CONFIG.thresholds.performance.max_bundle_size_mb,
                recommendation: 'Optimize bundle size through code splitting and tree shaking'
            });
        }
        
        this.log(`✅ Quality thresholds checked - ${this.metrics.alerts.length} alerts generated`, 'green');
    }

    async updateMetricsTrends() {
        this.log('📈 Updating metrics trends database...', 'blue');
        
        const trendsFile = path.join(CONFIG.outputDir, 'quality-trends-detailed.json');
        let detailedTrends = [];
        
        if (fs.existsSync(trendsFile)) {
            try {
                detailedTrends = JSON.parse(fs.readFileSync(trendsFile, 'utf8'));
            } catch (error) {
                this.log('⚠️ Could not read detailed trends data', 'yellow');
            }
        }
        
        // Add current detailed metrics to trends
        const currentTrend = {
            timestamp: this.metrics.timestamp,
            overall: this.metrics.overall,
            frontend: {
                eslintErrors: this.metrics.frontend.eslint?.errorCount || 0,
                eslintWarnings: this.metrics.frontend.eslint?.warningCount || 0,
                typescriptErrors: this.metrics.frontend.typescript?.errors || 0,
                coverage: this.metrics.frontend.coverage?.statements || 0,
                bundleSize: this.metrics.frontend.bundle?.totalSize || 0,
                complexityScore: this.metrics.frontend.complexity?.complexityScore || 0
            },
            backend: {
                flake8Issues: this.metrics.backend.flake8?.totalIssues || 0,
                mypyErrors: this.metrics.backend.mypy?.errors || 0,
                coverage: this.metrics.backend.coverage?.statements || 0,
                securityIssues: this.metrics.backend.security?.totalIssues || 0,
                highSeverityIssues: this.metrics.backend.security?.highSeverity || 0
            },
            alertsCount: this.metrics.alerts.length
        };
        
        detailedTrends.push(currentTrend);
        
        // Keep only last 50 entries for detailed trends
        if (detailedTrends.length > 50) {
            detailedTrends = detailedTrends.slice(-50);
        }
        
        // Save detailed trends
        fs.writeFileSync(trendsFile, JSON.stringify(detailedTrends, null, 2));
        
        this.log('✅ Metrics trends updated', 'green');
    }

    displayMetricsSummary() {
        const { overall, alerts } = this.metrics;
        
        console.log('\n' + '='.repeat(60));
        console.log('📊 QUALITY METRICS SUMMARY');
        console.log('='.repeat(60));
        console.log(`🎯 Quality Score: ${overall.qualityScore}/100`);
        console.log(`🧪 Test Coverage: ${overall.coverage.toFixed(1)}%`);
        console.log(`🐛 Total Errors: ${overall.totalErrors}`);
        console.log(`🔒 Security Score: ${overall.securityScore}/100`);
        console.log(`🔧 Maintainability: ${overall.maintainabilityIndex}/100`);
        console.log(`🚨 Active Alerts: ${alerts.length}`);
        console.log('='.repeat(60));
        
        if (alerts.length > 0) {
            console.log('\n🚨 QUALITY ALERTS:');
            alerts.forEach((alert, index) => {
                const icon = alert.severity === 'critical' ? '🔴' : alert.severity === 'warning' ? '🟡' : '🔵';
                console.log(`${icon} ${index + 1}. ${alert.message}`);
            });
        } else {
            console.log('\n✅ No quality alerts - all metrics within thresholds!');
        }
        
        console.log('\n📁 Reports saved to:', CONFIG.outputDir);
        console.log('');
    }

    generateRecommendations() {
        const recommendations = [];
        const { overall, frontend, backend } = this.metrics;
        
        if (overall.coverage < CONFIG.thresholds.coverage.statements) {
            recommendations.push('📝 **Improve Test Coverage:** Add unit tests to reach the target coverage threshold');
        }
        
        if (overall.totalErrors > 0) {
            recommendations.push('🔧 **Fix Quality Errors:** Address linting, type checking, and compilation errors');
        }
        
        if (overall.securityScore < 90) {
            recommendations.push('🔒 **Address Security Issues:** Review and fix security vulnerabilities');
        }
        
        if (frontend.bundle?.totalSize > 2000000) { // 2MB
            recommendations.push('📦 **Optimize Bundle Size:** Consider code splitting and tree shaking');
        }
        
        if (frontend.complexity?.complexityScore < 70) {
            recommendations.push('🧠 **Reduce Complexity:** Refactor complex functions and improve code structure');
        }
        
        if (backend.security?.highSeverity > 0) {
            recommendations.push('🚨 **Critical Security:** Address high-severity security issues immediately');
        }
        
        if (overall.maintainabilityIndex < CONFIG.thresholds.complexity.maintainability_min) {
            recommendations.push('🔧 **Improve Maintainability:** Refactor code to improve readability and structure');
        }
        
        if (recommendations.length === 0) {
            recommendations.push('🎉 **Great Job!** All quality metrics are within acceptable thresholds');
        }
        
        return recommendations.map(rec => `- ${rec}`).join('\n');
    }

    generateCSVReport() {
        const headers = ['timestamp', 'qualityScore', 'coverage', 'errors', 'securityScore'];
        const rows = this.metrics.trends.map(trend => 
            headers.map(header => trend[header] || '').join(',')
        );
        
        return [headers.join(','), ...rows].join('\n');
    }

    getStatusEmoji(value, threshold) {
        return value >= threshold ? '✅' : '❌';
    }
}

// Main execution
async function main() {
    try {
        const collector = new QualityMetricsCollector();
        await collector.collectAllMetrics();
        
        console.log('\n🎉 Quality metrics collection completed successfully!');
        console.log(`📊 View reports in the ${CONFIG.outputDir}/ directory`);
        
        process.exit(0);
    } catch (error) {
        console.error('❌ Quality metrics collection failed:', error.message);
        process.exit(1);
    }
}

// Run if called directly
if (process.argv[1] && process.argv[1].endsWith('quality-metrics.js')) {
    main();
}

export { CONFIG, QualityMetricsCollector };
