#!/usr/bin/env node

/**
 * @fileoverview Automated Documentation Maintenance System
 * Automatically updates and maintains project documentation including
 * API docs, README files, and code quality reports.
 * 
 * @author AI Scholar Team
 * @version 1.0.0
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { APIDocumentationGenerator } = require('./generate-api-docs');

/**
 * Configuration for documentation maintenance
 */
const config = {
  sourceDir: 'src',
  docsDir: 'docs',
  outputFormats: ['markdown', 'html', 'json'],
  updateFrequency: 'daily', // daily, weekly, on-change
  autoCommit: process.env.NODE_ENV === 'production',
  notifications: {
    slack: process.env.SLACK_WEBHOOK_URL,
    email: process.env.NOTIFICATION_EMAIL
  }
};

/**
 * Main documentation maintenance class
 */
class DocumentationMaintainer {
  constructor(options = {}) {
    this.config = { ...config, ...options };
    this.changes = [];
    this.errors = [];
  }

  /**
   * Run complete documentation maintenance
   * 
   * @returns {Promise<void>}
   */
  async maintain() {
    console.log('🔧 Starting documentation maintenance...');
    
    try {
      // Check for changes since last run
      const hasChanges = await this.detectChanges();
      
      if (!hasChanges && this.config.updateFrequency !== 'force') {
        console.log('📄 No changes detected, skipping maintenance');
        return;
      }
      
      // Update API documentation
      await this.updateAPIDocumentation();
      
      // Update README files
      await this.updateReadmeFiles();
      
      // Update code quality documentation
      await this.updateQualityDocumentation();
      
      // Validate documentation
      await this.validateDocumentation();
      
      // Generate documentation index
      await this.generateDocumentationIndex();
      
      // Commit changes if configured
      if (this.config.autoCommit && this.changes.length > 0) {
        await this.commitChanges();
      }
      
      // Send notifications
      await this.sendNotifications();
      
      console.log('✅ Documentation maintenance completed successfully!');
      
    } catch (error) {
      console.error('❌ Documentation maintenance failed:', error);
      this.errors.push(error);
      await this.sendErrorNotifications();
      process.exit(1);
    }
  }

  /**
   * Detect changes in source files since last documentation update
   * 
   * @returns {Promise<boolean>} Whether changes were detected
   */
  async detectChanges() {
    try {
      // Get last documentation update timestamp
      const lastUpdateFile = path.join(this.config.docsDir, '.last-update');
      let lastUpdate = new Date(0);
      
      if (fs.existsSync(lastUpdateFile)) {
        const timestamp = fs.readFileSync(lastUpdateFile, 'utf-8').trim();
        lastUpdate = new Date(timestamp);
      }
      
      // Check for changes in source files
      const sourceFiles = this.getSourceFiles();
      
      for (const file of sourceFiles) {
        const stats = fs.statSync(file);
        if (stats.mtime > lastUpdate) {
          console.log(`📝 Change detected in: ${file}`);
          return true;
        }
      }
      
      // Check for changes in package.json or other config files
      const configFiles = [
        'package.json',
        'backend/requirements.txt',
        'backend/pyproject.toml',
        'eslint.config.js',
        'tsconfig.json'
      ];
      
      for (const file of configFiles) {
        if (fs.existsSync(file)) {
          const stats = fs.statSync(file);
          if (stats.mtime > lastUpdate) {
            console.log(`⚙️  Config change detected in: ${file}`);
            return true;
          }
        }
      }
      
      return false;
      
    } catch (error) {
      console.warn('⚠️  Could not detect changes, proceeding with update:', error.message);
      return true;
    }
  }

  /**
   * Get all source files for change detection
   * 
   * @returns {string[]} Array of source file paths
   */
  getSourceFiles() {
    const files = [];
    
    const scanDirectory = (dir) => {
      if (!fs.existsSync(dir)) return;
      
      const items = fs.readdirSync(dir);
      
      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stats = fs.statSync(fullPath);
        
        if (stats.isDirectory()) {
          if (!item.startsWith('.') && item !== 'node_modules') {
            scanDirectory(fullPath);
          }
        } else if (this.isSourceFile(fullPath)) {
          files.push(fullPath);
        }
      }
    };
    
    scanDirectory(this.config.sourceDir);
    scanDirectory('backend');
    
    return files;
  }

  /**
   * Check if file is a source file that should trigger documentation updates
   * 
   * @param {string} filePath - Path to check
   * @returns {boolean} Whether file is a source file
   */
  isSourceFile(filePath) {
    const ext = path.extname(filePath);
    return ['.ts', '.tsx', '.js', '.jsx', '.py'].includes(ext);
  }

  /**
   * Update API documentation
   * 
   * @returns {Promise<void>}
   */
  async updateAPIDocumentation() {
    console.log('📚 Updating API documentation...');
    
    try {
      const generator = new APIDocumentationGenerator({
        sourceDir: this.config.sourceDir,
        outputDir: path.join(this.config.docsDir, 'api'),
        formats: this.config.outputFormats
      });
      
      await generator.generate();
      this.changes.push('Updated API documentation');
      
    } catch (error) {
      console.error('Failed to update API documentation:', error);
      this.errors.push(error);
    }
  }

  /**
   * Update README files throughout the project
   * 
   * @returns {Promise<void>}
   */
  async updateReadmeFiles() {
    console.log('📖 Updating README files...');
    
    try {
      // Update main README
      await this.updateMainReadme();
      
      // Update component READMEs
      await this.updateComponentReadmes();
      
      // Update service READMEs
      await this.updateServiceReadmes();
      
      this.changes.push('Updated README files');
      
    } catch (error) {
      console.error('Failed to update README files:', error);
      this.errors.push(error);
    }
  }

  /**
   * Update main project README
   * 
   * @returns {Promise<void>}
   */
  async updateMainReadme() {
    const readmePath = 'README.md';
    
    if (!fs.existsSync(readmePath)) {
      console.log('📝 Creating main README.md...');
      
      const readmeContent = this.generateMainReadme();
      fs.writeFileSync(readmePath, readmeContent);
      
      return;
    }
    
    // Update existing README with current information
    let content = fs.readFileSync(readmePath, 'utf-8');
    
    // Update badges section
    content = this.updateReadmeBadges(content);
    
    // Update table of contents
    content = this.updateTableOfContents(content);
    
    // Update installation instructions
    content = this.updateInstallationInstructions(content);
    
    fs.writeFileSync(readmePath, content);
  }

  /**
   * Generate main README content
   * 
   * @returns {string} README content
   */
  generateMainReadme() {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf-8'));
    
    return `# ${packageJson.name}

${packageJson.description || 'AI Scholar RAG Chatbot - Advanced research assistance and document analysis'}

## 🚀 Features

- **Intelligent Document Processing**: Upload and analyze academic papers, research documents
- **Advanced Search**: Hybrid search combining semantic and keyword search
- **Multi-modal Support**: Handle text, images, charts, and tables
- **Real-time Analytics**: Comprehensive performance monitoring
- **Voice Interaction**: Voice commands and speech-to-text
- **Personalization**: Adaptive learning and recommendations

## 🛠️ Technology Stack

### Frontend
- React 18 with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- React Query for data fetching

### Backend
- Python 3.11 with FastAPI
- PostgreSQL for primary database
- Redis for caching
- Elasticsearch for search

## 📋 Prerequisites

- Node.js 18+
- Python 3.11+
- Docker and Docker Compose
- Git

## 🚀 Quick Start

1. **Clone the repository**:
   \`\`\`bash
   git clone https://github.com/your-org/ai-scholar-chatbot.git
   cd ai-scholar-chatbot
   \`\`\`

2. **Install dependencies**:
   \`\`\`bash
   npm install
   cd backend && pip install -r requirements-dev.txt
   \`\`\`

3. **Start development services**:
   \`\`\`bash
   docker-compose up -d
   \`\`\`

4. **Run the application**:
   \`\`\`bash
   npm run dev  # Frontend
   cd backend && python app.py  # Backend
   \`\`\`

## 📚 Documentation

- [Developer Onboarding](docs/DEVELOPER_ONBOARDING.md)
- [Code Quality Guidelines](docs/CODE_QUALITY_GUIDELINES.md)
- [API Documentation](docs/api/)
- [Component Documentation](src/components/README.md)

## 🧪 Testing

\`\`\`bash
# Frontend tests
npm test

# Backend tests
cd backend && pytest
\`\`\`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

See [DEVELOPER_ONBOARDING.md](docs/DEVELOPER_ONBOARDING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/your-org/ai-scholar-chatbot/issues)
- Discussions: [GitHub Discussions](https://github.com/your-org/ai-scholar-chatbot/discussions)

---

*Last updated: ${new Date().toISOString().split('T')[0]}*
`;
  }

  /**
   * Update README badges section
   * 
   * @param {string} content - Current README content
   * @returns {string} Updated content
   */
  updateReadmeBadges(content) {
    const badges = [
      '![Build Status](https://github.com/your-org/ai-scholar-chatbot/workflows/CI/badge.svg)',
      '![Coverage](https://codecov.io/gh/your-org/ai-scholar-chatbot/branch/main/graph/badge.svg)',
      '![License](https://img.shields.io/badge/license-MIT-blue.svg)',
      '![Node Version](https://img.shields.io/badge/node-%3E%3D18-brightgreen.svg)',
      '![Python Version](https://img.shields.io/badge/python-%3E%3D3.11-brightgreen.svg)'
    ].join('\n');
    
    // Replace existing badges or add them after the title
    const badgeRegex = /!\[.*?\]\(.*?\)/g;
    
    if (content.match(badgeRegex)) {
      return content.replace(badgeRegex, '').replace(/\n+/, '\n\n' + badges + '\n\n');
    } else {
      return content.replace(/^(# .*?\n)/, `$1\n${badges}\n\n`);
    }
  }

  /**
   * Update table of contents
   * 
   * @param {string} content - Current README content
   * @returns {string} Updated content
   */
  updateTableOfContents(content) {
    // Extract headers from content
    const headers = content.match(/^#{1,6}\s+(.+)$/gm) || [];
    
    if (headers.length === 0) return content;
    
    const toc = headers
      .filter(header => !header.startsWith('# ')) // Skip main title
      .map(header => {
        const level = header.match(/^#+/)[0].length;
        const text = header.replace(/^#+\s+/, '').replace(/[^\w\s-]/g, '');
        const link = text.toLowerCase().replace(/\s+/g, '-');
        const indent = '  '.repeat(level - 2);
        
        return `${indent}- [${text}](#${link})`;
      })
      .join('\n');
    
    // Replace existing TOC or add after description
    const tocRegex = /## Table of Contents[\s\S]*?(?=\n## |\n# |$)/;
    
    if (content.match(tocRegex)) {
      return content.replace(tocRegex, `## Table of Contents\n\n${toc}\n\n`);
    }
    
    return content;
  }

  /**
   * Update installation instructions
   * 
   * @param {string} content - Current README content
   * @returns {string} Updated content
   */
  updateInstallationInstructions(content) {
    // Get current Node.js and Python versions from package files
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf-8'));
    const nodeVersion = packageJson.engines?.node || '18+';
    
    let pythonVersion = '3.11+';
    try {
      const pyprojectPath = 'backend/pyproject.toml';
      if (fs.existsSync(pyprojectPath)) {
        const pyproject = fs.readFileSync(pyprojectPath, 'utf-8');
        const versionMatch = pyproject.match(/python = "(.+)"/);
        if (versionMatch) {
          pythonVersion = versionMatch[1];
        }
      }
    } catch (error) {
      console.warn('Could not read Python version from pyproject.toml');
    }
    
    // Update version requirements in prerequisites section
    content = content.replace(
      /Node\.js \d+[\.\d]*\+?/g,
      `Node.js ${nodeVersion}`
    );
    
    content = content.replace(
      /Python \d+[\.\d]*\+?/g,
      `Python ${pythonVersion}`
    );
    
    return content;
  }

  /**
   * Update component README files
   * 
   * @returns {Promise<void>}
   */
  async updateComponentReadmes() {
    const componentsDir = path.join(this.config.sourceDir, 'components');
    
    if (!fs.existsSync(componentsDir)) return;
    
    // Update main components README
    const readmePath = path.join(componentsDir, 'README.md');
    
    if (fs.existsSync(readmePath)) {
      let content = fs.readFileSync(readmePath, 'utf-8');
      
      // Update component list
      content = this.updateComponentList(content, componentsDir);
      
      fs.writeFileSync(readmePath, content);
    }
  }

  /**
   * Update component list in README
   * 
   * @param {string} content - Current README content
   * @param {string} componentsDir - Components directory path
   * @returns {string} Updated content
   */
  updateComponentList(content, componentsDir) {
    const components = fs.readdirSync(componentsDir)
      .filter(file => file.endsWith('.tsx') || file.endsWith('.ts'))
      .filter(file => !file.includes('.test.') && !file.includes('.spec.'))
      .map(file => {
        const name = path.basename(file, path.extname(file));
        const filePath = path.join(componentsDir, file);
        
        // Try to extract component description from JSDoc
        let description = 'No description available';
        try {
          const fileContent = fs.readFileSync(filePath, 'utf-8');
          const docMatch = fileContent.match(/\/\*\*[\s\S]*?\*\s*([^@\n].*?)(?:\n\s*\*\s*@|\n\s*\*\/)/);
          if (docMatch) {
            description = docMatch[1].replace(/\n\s*\*\s*/g, ' ').trim();
          }
        } catch (error) {
          // Ignore errors reading file
        }
        
        return `- **[${name}](./${file})**: ${description}`;
      })
      .join('\n');
    
    // Replace component list section
    const listRegex = /### Core Application Components[\s\S]*?(?=\n### |\n## |$)/;
    
    if (content.match(listRegex)) {
      return content.replace(
        listRegex,
        `### Core Application Components\n\n${components}\n\n`
      );
    }
    
    return content;
  }

  /**
   * Update service README files
   * 
   * @returns {Promise<void>}
   */
  async updateServiceReadmes() {
    const servicesDir = path.join(this.config.sourceDir, 'services');
    
    if (!fs.existsSync(servicesDir)) return;
    
    // Update main services README
    const readmePath = path.join(servicesDir, 'README.md');
    
    if (fs.existsSync(readmePath)) {
      let content = fs.readFileSync(readmePath, 'utf-8');
      
      // Update service list
      content = this.updateServiceList(content, servicesDir);
      
      fs.writeFileSync(readmePath, content);
    }
  }

  /**
   * Update service list in README
   * 
   * @param {string} content - Current README content
   * @param {string} servicesDir - Services directory path
   * @returns {string} Updated content
   */
  updateServiceList(content, servicesDir) {
    const services = fs.readdirSync(servicesDir)
      .filter(file => file.endsWith('.ts') && !file.includes('.test.'))
      .map(file => {
        const name = path.basename(file, '.ts');
        const filePath = path.join(servicesDir, file);
        
        // Try to extract service description from JSDoc
        let description = 'No description available';
        try {
          const fileContent = fs.readFileSync(filePath, 'utf-8');
          const docMatch = fileContent.match(/\/\*\*[\s\S]*?\*\s*([^@\n].*?)(?:\n\s*\*\s*@|\n\s*\*\/)/);
          if (docMatch) {
            description = docMatch[1].replace(/\n\s*\*\s*/g, ' ').trim();
          }
        } catch (error) {
          // Ignore errors reading file
        }
        
        return `- **[${name}](./${file})**: ${description}`;
      })
      .join('\n');
    
    // Update service categories in README
    const categories = {
      'Analytics & Insights': services.filter(s => s.includes('analytics') || s.includes('chart') || s.includes('error')),
      'Content & Document Processing': services.filter(s => s.includes('citation') || s.includes('document') || s.includes('modal')),
      'Search & Retrieval': services.filter(s => s.includes('search') || s.includes('memory')),
      'User Experience': services.filter(s => s.includes('personalization') || s.includes('voice') || s.includes('accessibility')),
      'Integration & Workflow': services.filter(s => s.includes('integration') || s.includes('workflow') || s.includes('plugin')),
      'Security & Monitoring': services.filter(s => s.includes('security') || s.includes('bias'))
    };
    
    let updatedContent = content;
    
    Object.entries(categories).forEach(([category, categoryServices]) => {
      if (categoryServices.length > 0) {
        const categoryRegex = new RegExp(`### ${category}[\\s\\S]*?(?=\\n### |\\n## |$)`);
        const categoryContent = `### ${category}\n\n${categoryServices.join('\n')}\n\n`;
        
        if (updatedContent.match(categoryRegex)) {
          updatedContent = updatedContent.replace(categoryRegex, categoryContent);
        }
      }
    });
    
    return updatedContent;
  }

  /**
   * Update code quality documentation
   * 
   * @returns {Promise<void>}
   */
  async updateQualityDocumentation() {
    console.log('📊 Updating code quality documentation...');
    
    try {
      // Generate quality metrics report
      await this.generateQualityMetricsReport();
      
      // Update quality guidelines if needed
      await this.updateQualityGuidelines();
      
      this.changes.push('Updated code quality documentation');
      
    } catch (error) {
      console.error('Failed to update quality documentation:', error);
      this.errors.push(error);
    }
  }

  /**
   * Generate quality metrics report
   * 
   * @returns {Promise<void>}
   */
  async generateQualityMetricsReport() {
    try {
      // Run quality metrics collection
      const metricsScript = path.join(__dirname, 'quality-metrics.js');
      
      if (fs.existsSync(metricsScript)) {
        execSync(`node ${metricsScript}`, { stdio: 'inherit' });
      }
      
    } catch (error) {
      console.warn('Could not generate quality metrics report:', error.message);
    }
  }

  /**
   * Update quality guidelines
   * 
   * @returns {Promise<void>}
   */
  async updateQualityGuidelines() {
    const guidelinesPath = path.join(this.config.docsDir, 'CODE_QUALITY_GUIDELINES.md');
    
    if (!fs.existsSync(guidelinesPath)) return;
    
    let content = fs.readFileSync(guidelinesPath, 'utf-8');
    
    // Update last modified date
    content = content.replace(
      /Last updated: .*/,
      `Last updated: ${new Date().toISOString().split('T')[0]}`
    );
    
    fs.writeFileSync(guidelinesPath, content);
  }

  /**
   * Validate documentation for consistency and completeness
   * 
   * @returns {Promise<void>}
   */
  async validateDocumentation() {
    console.log('✅ Validating documentation...');
    
    const validationErrors = [];
    
    // Check for broken links
    const brokenLinks = await this.findBrokenLinks();
    if (brokenLinks.length > 0) {
      validationErrors.push(`Broken links found: ${brokenLinks.join(', ')}`);
    }
    
    // Check for missing documentation
    const missingDocs = await this.findMissingDocumentation();
    if (missingDocs.length > 0) {
      validationErrors.push(`Missing documentation: ${missingDocs.join(', ')}`);
    }
    
    // Check for outdated documentation
    const outdatedDocs = await this.findOutdatedDocumentation();
    if (outdatedDocs.length > 0) {
      validationErrors.push(`Outdated documentation: ${outdatedDocs.join(', ')}`);
    }
    
    if (validationErrors.length > 0) {
      console.warn('⚠️  Documentation validation warnings:');
      validationErrors.forEach(error => console.warn(`  - ${error}`));
      this.errors.push(...validationErrors);
    } else {
      console.log('✅ Documentation validation passed');
    }
  }

  /**
   * Find broken links in documentation
   * 
   * @returns {Promise<string[]>} Array of broken links
   */
  async findBrokenLinks() {
    const brokenLinks = [];
    
    // This is a simplified implementation
    // In a real scenario, you'd want to use a proper link checker
    
    return brokenLinks;
  }

  /**
   * Find missing documentation
   * 
   * @returns {Promise<string[]>} Array of missing documentation items
   */
  async findMissingDocumentation() {
    const missing = [];
    
    // Check for components without documentation
    const componentsDir = path.join(this.config.sourceDir, 'components');
    if (fs.existsSync(componentsDir)) {
      const components = fs.readdirSync(componentsDir)
        .filter(file => file.endsWith('.tsx'))
        .filter(file => !file.includes('.test.'));
      
      for (const component of components) {
        const componentPath = path.join(componentsDir, component);
        const content = fs.readFileSync(componentPath, 'utf-8');
        
        // Check if component has JSDoc documentation
        if (!content.includes('/**')) {
          missing.push(`Component ${component} missing JSDoc documentation`);
        }
      }
    }
    
    return missing;
  }

  /**
   * Find outdated documentation
   * 
   * @returns {Promise<string[]>} Array of outdated documentation items
   */
  async findOutdatedDocumentation() {
    const outdated = [];
    
    // Check if documentation is older than source files
    const docsFiles = this.getDocumentationFiles();
    const sourceFiles = this.getSourceFiles();
    
    for (const docFile of docsFiles) {
      const docStats = fs.statSync(docFile);
      
      // Find related source files
      const relatedSources = sourceFiles.filter(source => {
        const docName = path.basename(docFile, '.md').toLowerCase();
        const sourceName = path.basename(source).toLowerCase();
        return sourceName.includes(docName) || docName.includes(sourceName.split('.')[0]);
      });
      
      for (const source of relatedSources) {
        const sourceStats = fs.statSync(source);
        if (sourceStats.mtime > docStats.mtime) {
          outdated.push(`${docFile} is older than ${source}`);
        }
      }
    }
    
    return outdated;
  }

  /**
   * Get all documentation files
   * 
   * @returns {string[]} Array of documentation file paths
   */
  getDocumentationFiles() {
    const files = [];
    
    const scanDirectory = (dir) => {
      if (!fs.existsSync(dir)) return;
      
      const items = fs.readdirSync(dir);
      
      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stats = fs.statSync(fullPath);
        
        if (stats.isDirectory()) {
          if (!item.startsWith('.')) {
            scanDirectory(fullPath);
          }
        } else if (item.endsWith('.md')) {
          files.push(fullPath);
        }
      }
    };
    
    scanDirectory(this.config.docsDir);
    scanDirectory(this.config.sourceDir);
    
    return files;
  }

  /**
   * Generate documentation index
   * 
   * @returns {Promise<void>}
   */
  async generateDocumentationIndex() {
    console.log('📋 Generating documentation index...');
    
    const indexPath = path.join(this.config.docsDir, 'INDEX.md');
    const indexContent = this.generateIndexContent();
    
    fs.writeFileSync(indexPath, indexContent);
    this.changes.push('Generated documentation index');
  }

  /**
   * Generate documentation index content
   * 
   * @returns {string} Index content
   */
  generateIndexContent() {
    const docs = this.getDocumentationFiles()
      .map(file => {
        const relativePath = path.relative(this.config.docsDir, file);
        const name = path.basename(file, '.md');
        
        // Try to extract description from file
        let description = 'No description available';
        try {
          const content = fs.readFileSync(file, 'utf-8');
          const firstParagraph = content.split('\n').find(line => 
            line.trim() && !line.startsWith('#') && !line.startsWith('>')
          );
          if (firstParagraph) {
            description = firstParagraph.trim();
          }
        } catch (error) {
          // Ignore errors
        }
        
        return { name, path: relativePath, description };
      })
      .sort((a, b) => a.name.localeCompare(b.name));
    
    return `# Documentation Index

This is an automatically generated index of all documentation in the project.

*Last updated: ${new Date().toISOString()}*

## Available Documentation

${docs.map(doc => `### [${doc.name}](${doc.path})

${doc.description}

`).join('')}

## Quick Links

- [Developer Onboarding](DEVELOPER_ONBOARDING.md) - Get started with development
- [Code Quality Guidelines](CODE_QUALITY_GUIDELINES.md) - Coding standards and best practices
- [API Documentation](api/) - Complete API reference
- [Component Documentation](../src/components/README.md) - React component documentation
- [Services Documentation](../src/services/README.md) - Service layer documentation

## Contributing to Documentation

To contribute to documentation:

1. Follow the documentation standards in the Code Quality Guidelines
2. Use clear, concise language
3. Include examples where appropriate
4. Keep documentation up to date with code changes
5. Run \`npm run docs:maintain\` to update generated documentation

## Maintenance

This documentation is automatically maintained by the documentation maintenance system. 
To manually trigger an update, run:

\`\`\`bash
npm run docs:maintain
\`\`\`
`;
  }

  /**
   * Commit documentation changes
   * 
   * @returns {Promise<void>}
   */
  async commitChanges() {
    console.log('💾 Committing documentation changes...');
    
    try {
      // Update last update timestamp
      const lastUpdateFile = path.join(this.config.docsDir, '.last-update');
      fs.writeFileSync(lastUpdateFile, new Date().toISOString());
      
      // Stage changes
      execSync('git add docs/ src/*/README.md README.md', { stdio: 'inherit' });
      
      // Check if there are changes to commit
      const status = execSync('git status --porcelain', { encoding: 'utf-8' });
      
      if (status.trim()) {
        // Commit changes
        const commitMessage = `docs: automated documentation update

${this.changes.join('\n')}

Generated by documentation maintenance system`;
        
        execSync(`git commit -m "${commitMessage}"`, { stdio: 'inherit' });
        console.log('✅ Documentation changes committed');
      } else {
        console.log('📄 No changes to commit');
      }
      
    } catch (error) {
      console.error('Failed to commit changes:', error);
      this.errors.push(error);
    }
  }

  /**
   * Send notifications about documentation updates
   * 
   * @returns {Promise<void>}
   */
  async sendNotifications() {
    if (this.changes.length === 0) return;
    
    const message = `📚 Documentation Updated

${this.changes.join('\n')}

Updated at: ${new Date().toISOString()}`;
    
    // Send Slack notification
    if (this.config.notifications.slack) {
      try {
        await this.sendSlackNotification(message);
      } catch (error) {
        console.warn('Failed to send Slack notification:', error.message);
      }
    }
    
    // Send email notification
    if (this.config.notifications.email) {
      try {
        await this.sendEmailNotification(message);
      } catch (error) {
        console.warn('Failed to send email notification:', error.message);
      }
    }
  }

  /**
   * Send error notifications
   * 
   * @returns {Promise<void>}
   */
  async sendErrorNotifications() {
    if (this.errors.length === 0) return;
    
    const message = `❌ Documentation Maintenance Errors

${this.errors.join('\n')}

Failed at: ${new Date().toISOString()}`;
    
    console.error(message);
    
    // Send notifications about errors
    if (this.config.notifications.slack) {
      try {
        await this.sendSlackNotification(message);
      } catch (error) {
        console.warn('Failed to send error notification to Slack:', error.message);
      }
    }
  }

  /**
   * Send Slack notification
   * 
   * @param {string} message - Message to send
   * @returns {Promise<void>}
   */
  async sendSlackNotification(message) {
    const fetch = (await import('node-fetch')).default;
    
    await fetch(this.config.notifications.slack, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: message })
    });
  }

  /**
   * Send email notification
   * 
   * @param {string} message - Message to send
   * @returns {Promise<void>}
   */
  async sendEmailNotification(message) {
    // Implementation would depend on email service used
    console.log('Email notification:', message);
  }
}

// CLI interface
if (require.main === module) {
  const maintainer = new DocumentationMaintainer();
  maintainer.maintain().catch(console.error);
}

module.exports = { DocumentationMaintainer };