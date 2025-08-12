#!/usr/bin/env node

/**
 * AI Scholar RAG Chatbot - Quality Configuration Validator
 * 
 * This script validates the quality configuration and ensures all
 * thresholds and settings are properly configured.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class QualityConfigValidator {
    constructor() {
        this.configFile = 'quality-config.json';
        this.errors = [];
        this.warnings = [];
        this.config = null;
    }

    async validateConfiguration() {
        console.log('🔍 Validating quality configuration...');
        
        try {
            await this.loadConfiguration();
            await this.validateConfigStructure();
            await this.validateThresholds();
            await this.validateIntegrations();
            await this.validateReporting();
            await this.validateAlerts();
            await this.generateValidationReport();
            
            this.displayResults();
            
            return this.errors.length === 0;
        } catch (error) {
            console.error(`❌ Configuration validation failed: ${error.message}`);
            return false;
        }
    }

    async loadConfiguration() {
        if (!fs.existsSync(this.configFile)) {
            this.errors.push(`Configuration file ${this.configFile} not found`);
            return;
        }

        try {
            const configData = fs.readFileSync(this.configFile, 'utf8');
            this.config = JSON.parse(configData);
            console.log('✅ Configuration file loaded successfully');
        } catch (error) {
            this.errors.push(`Invalid JSON in configuration file: ${error.message}`);
        }
    }

    async validateConfigStructure() {
        if (!this.config) return;

        const requiredSections = [
            'version',
            'project',
            'quality_gates',
            'thresholds',
            'frontend',
            'backend',
            'reporting',
            'alerts',
            'automation'
        ];

        requiredSections.forEach(section => {
            if (!this.config[section]) {
                this.errors.push(`Missing required configuration section: ${section}`);
            }
        });

        console.log('✅ Configuration structure validated');
    }

    async validateThresholds() {
        if (!this.config?.thresholds) return;

        const thresholds = this.config.thresholds;

        // Validate quality score thresholds
        if (thresholds.quality_score) {
            const qs = thresholds.quality_score;
            if (qs.excellent <= qs.good || qs.good <= qs.warning || qs.warning <= qs.critical) {
                this.errors.push('Quality score thresholds must be in descending order (excellent > good > warning > critical)');
            }
            if (qs.critical < 0 || qs.excellent > 100) {
                this.errors.push('Quality score thresholds must be between 0 and 100');
            }
        }

        // Validate coverage thresholds
        if (thresholds.coverage) {
            const coverage = thresholds.coverage;
            ['statements', 'branches', 'functions', 'lines'].forEach(metric => {
                if (coverage[metric] && (coverage[metric] < 0 || coverage[metric] > 100)) {
                    this.errors.push(`Coverage threshold for ${metric} must be between 0 and 100`);
                }
            });
        }

        // Validate complexity thresholds
        if (thresholds.complexity) {
            const complexity = thresholds.complexity;
            if (complexity.cyclomatic_max && complexity.cyclomatic_max < 1) {
                this.errors.push('Cyclomatic complexity threshold must be at least 1');
            }
            if (complexity.maintainability_min && (complexity.maintainability_min < 0 || complexity.maintainability_min > 100)) {
                this.errors.push('Maintainability threshold must be between 0 and 100');
            }
        }

        // Validate security thresholds
        if (thresholds.security) {
            const security = thresholds.security;
            if (security.min_score && (security.min_score < 0 || security.min_score > 100)) {
                this.errors.push('Security score threshold must be between 0 and 100');
            }
            if (security.max_high_severity && security.max_high_severity < 0) {
                this.errors.push('Maximum high severity issues must be non-negative');
            }
        }

        // Validate performance thresholds
        if (thresholds.performance) {
            const perf = thresholds.performance;
            if (perf.max_bundle_size_mb && perf.max_bundle_size_mb <= 0) {
                this.errors.push('Maximum bundle size must be positive');
            }
            if (perf.max_build_time_seconds && perf.max_build_time_seconds <= 0) {
                this.errors.push('Maximum build time must be positive');
            }
        }

        console.log('✅ Thresholds validated');
    }

    async validateIntegrations() {
        if (!this.config?.integrations) return;

        const integrations = this.config.integrations;

        // Validate CodeCov integration
        if (integrations.codecov?.enabled && !integrations.codecov.token) {
            this.warnings.push('CodeCov is enabled but no token is configured');
        }

        // Validate SonarQube integration
        if (integrations.sonarqube?.enabled) {
            if (!integrations.sonarqube.server_url) {
                this.errors.push('SonarQube is enabled but no server URL is configured');
            }
            if (!integrations.sonarqube.token) {
                this.warnings.push('SonarQube is enabled but no token is configured');
            }
        }

        console.log('✅ Integrations validated');
    }

    async validateReporting() {
        if (!this.config?.reporting) return;

        const reporting = this.config.reporting;

        if (reporting.retention_days && reporting.retention_days < 1) {
            this.errors.push('Report retention days must be at least 1');
        }

        if (reporting.output_directory && !this.isValidPath(reporting.output_directory)) {
            this.warnings.push('Output directory path may not be valid');
        }

        console.log('✅ Reporting configuration validated');
    }

    async validateAlerts() {
        if (!this.config?.alerts) return;

        const alerts = this.config.alerts;

        // Validate email configuration
        if (alerts.channels?.email?.enabled) {
            const email = alerts.channels.email;
            if (!email.smtp_server) {
                this.errors.push('Email alerts enabled but SMTP server not configured');
            }
            if (!email.recipients || email.recipients.length === 0) {
                this.warnings.push('Email alerts enabled but no recipients configured');
            }
        }

        // Validate Slack configuration
        if (alerts.channels?.slack?.enabled) {
            const slack = alerts.channels.slack;
            if (!slack.webhook_url) {
                this.errors.push('Slack alerts enabled but webhook URL not configured');
            }
        }

        // Validate webhook configuration
        if (alerts.channels?.webhook?.enabled) {
            const webhook = alerts.channels.webhook;
            if (!webhook.url) {
                this.errors.push('Webhook alerts enabled but URL not configured');
            }
        }

        // Validate alert conditions
        if (alerts.conditions) {
            const conditions = alerts.conditions;
            if (conditions.quality_score_below && (conditions.quality_score_below < 0 || conditions.quality_score_below > 100)) {
                this.errors.push('Quality score alert threshold must be between 0 and 100');
            }
            if (conditions.coverage_below && (conditions.coverage_below < 0 || conditions.coverage_below > 100)) {
                this.errors.push('Coverage alert threshold must be between 0 and 100');
            }
        }

        console.log('✅ Alerts configuration validated');
    }

    async generateValidationReport() {
        const reportDir = 'quality-reports';
        if (!fs.existsSync(reportDir)) {
            fs.mkdirSync(reportDir, { recursive: true });
        }

        const report = {
            timestamp: new Date().toISOString(),
            configFile: this.configFile,
            validation: {
                passed: this.errors.length === 0,
                errors: this.errors,
                warnings: this.warnings
            },
            recommendations: this.generateRecommendations()
        };

        const reportFile = path.join(reportDir, `config-validation-${Date.now()}.json`);
        fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));

        console.log(`📄 Validation report saved: ${reportFile}`);
    }

    generateRecommendations() {
        const recommendations = [];

        if (this.config?.thresholds?.coverage?.statements < 80) {
            recommendations.push('Consider increasing coverage threshold to at least 80% for better code quality');
        }

        if (this.config?.thresholds?.security?.max_high_severity > 0) {
            recommendations.push('Consider setting maximum high severity security issues to 0 for better security');
        }

        if (!this.config?.alerts?.enabled) {
            recommendations.push('Enable alerts to get notified about quality regressions');
        }

        if (!this.config?.automation?.ci_cd?.run_on_pull_request) {
            recommendations.push('Enable quality checks on pull requests to catch issues early');
        }

        if (this.config?.thresholds?.performance?.max_bundle_size_mb > 5) {
            recommendations.push('Consider reducing maximum bundle size threshold for better performance');
        }

        return recommendations;
    }

    isValidPath(pathStr) {
        try {
            path.resolve(pathStr);
            return true;
        } catch (error) {
            return false;
        }
    }

    displayResults() {
        console.log('\n' + '='.repeat(60));
        console.log('📊 QUALITY CONFIGURATION VALIDATION RESULTS');
        console.log('='.repeat(60));

        if (this.errors.length === 0) {
            console.log('✅ Configuration validation PASSED');
        } else {
            console.log('❌ Configuration validation FAILED');
        }

        console.log(`🔴 Errors: ${this.errors.length}`);
        console.log(`🟡 Warnings: ${this.warnings.length}`);

        if (this.errors.length > 0) {
            console.log('\n🔴 ERRORS:');
            this.errors.forEach((error, index) => {
                console.log(`  ${index + 1}. ${error}`);
            });
        }

        if (this.warnings.length > 0) {
            console.log('\n🟡 WARNINGS:');
            this.warnings.forEach((warning, index) => {
                console.log(`  ${index + 1}. ${warning}`);
            });
        }

        const recommendations = this.generateRecommendations();
        if (recommendations.length > 0) {
            console.log('\n💡 RECOMMENDATIONS:');
            recommendations.forEach((rec, index) => {
                console.log(`  ${index + 1}. ${rec}`);
            });
        }

        console.log('='.repeat(60));
    }
}

// Main execution
async function main() {
    try {
        const validator = new QualityConfigValidator();
        const isValid = await validator.validateConfiguration();
        
        process.exit(isValid ? 0 : 1);
    } catch (error) {
        console.error('❌ Configuration validation failed:', error.message);
        process.exit(1);
    }
}

// Run if called directly
if (process.argv[1] && process.argv[1].endsWith('quality-config-validator.js')) {
    main();
}

export { QualityConfigValidator };
