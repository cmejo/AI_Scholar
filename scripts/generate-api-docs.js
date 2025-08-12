#!/usr/bin/env node

/**
 * @fileoverview API Documentation Generator
 * Generates comprehensive API documentation from TypeScript source files
 * using JSDoc comments and TypeScript type information.
 * 
 * @author AI Scholar Team
 * @version 1.0.0
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

/**
 * Configuration for documentation generation
 */
const config = {
  sourceDir: 'src',
  outputDir: 'docs/api',
  includePatterns: ['**/*.ts', '**/*.tsx'],
  excludePatterns: ['**/*.test.ts', '**/*.spec.ts', '**/__tests__/**'],
  formats: ['html', 'markdown', 'json'],
  includePrivate: false,
  includeInternal: false,
  theme: 'default'
};

/**
 * Main documentation generator class
 */
class APIDocumentationGenerator {
  constructor(options = {}) {
    this.config = { ...config, ...options };
    this.sourceFiles = [];
    this.apiData = {
      services: [],
      components: [],
      types: [],
      utilities: [],
      hooks: []
    };
  }

  /**
   * Generate complete API documentation
   * 
   * @returns {Promise<void>}
   */
  async generate() {
    console.log('🚀 Starting API documentation generation...');
    
    try {
      // Ensure output directory exists
      this.ensureOutputDirectory();
      
      // Discover source files
      await this.discoverSourceFiles();
      
      // Parse TypeScript files
      await this.parseSourceFiles();
      
      // Generate documentation in multiple formats
      await this.generateDocumentation();
      
      // Generate index files
      await this.generateIndexFiles();
      
      console.log('✅ API documentation generated successfully!');
      console.log(`📁 Output directory: ${this.config.outputDir}`);
      
    } catch (error) {
      console.error('❌ Error generating API documentation:', error);
      process.exit(1);
    }
  }

  /**
   * Ensure output directory exists
   */
  ensureOutputDirectory() {
    if (!fs.existsSync(this.config.outputDir)) {
      fs.mkdirSync(this.config.outputDir, { recursive: true });
    }
    
    // Create subdirectories for different formats
    this.config.formats.forEach(format => {
      const formatDir = path.join(this.config.outputDir, format);
      if (!fs.existsSync(formatDir)) {
        fs.mkdirSync(formatDir, { recursive: true });
      }
    });
  }

  /**
   * Discover all TypeScript source files
   * 
   * @returns {Promise<void>}
   */
  async discoverSourceFiles() {
    console.log('🔍 Discovering source files...');
    
    const findFiles = (dir, files = []) => {
      const items = fs.readdirSync(dir);
      
      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);
        
        if (stat.isDirectory()) {
          // Skip node_modules and other excluded directories
          if (!item.startsWith('.') && item !== 'node_modules') {
            findFiles(fullPath, files);
          }
        } else if (this.shouldIncludeFile(fullPath)) {
          files.push(fullPath);
        }
      }
      
      return files;
    };
    
    this.sourceFiles = findFiles(this.config.sourceDir);
    console.log(`📄 Found ${this.sourceFiles.length} source files`);
  }

  /**
   * Check if file should be included in documentation
   * 
   * @param {string} filePath - Path to the file
   * @returns {boolean} Whether to include the file
   */
  shouldIncludeFile(filePath) {
    const ext = path.extname(filePath);
    if (!['.ts', '.tsx'].includes(ext)) return false;
    
    // Check exclude patterns
    for (const pattern of this.config.excludePatterns) {
      if (this.matchesPattern(filePath, pattern)) {
        return false;
      }
    }
    
    return true;
  }

  /**
   * Simple pattern matching for file paths
   * 
   * @param {string} filePath - File path to test
   * @param {string} pattern - Pattern to match against
   * @returns {boolean} Whether the pattern matches
   */
  matchesPattern(filePath, pattern) {
    const regex = new RegExp(
      pattern
        .replace(/\*\*/g, '.*')
        .replace(/\*/g, '[^/]*')
        .replace(/\?/g, '.')
    );
    return regex.test(filePath);
  }

  /**
   * Parse all source files and extract API information
   * 
   * @returns {Promise<void>}
   */
  async parseSourceFiles() {
    console.log('📖 Parsing source files...');
    
    for (const filePath of this.sourceFiles) {
      try {
        await this.parseFile(filePath);
      } catch (error) {
        console.warn(`⚠️  Warning: Could not parse ${filePath}:`, error.message);
      }
    }
  }

  /**
   * Parse a single TypeScript file
   * 
   * @param {string} filePath - Path to the file to parse
   * @returns {Promise<void>}
   */
  async parseFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf-8');
    const relativePath = path.relative(this.config.sourceDir, filePath);
    
    // Determine file category
    const category = this.categorizeFile(relativePath);
    
    // Extract JSDoc comments and TypeScript definitions
    const apiInfo = this.extractAPIInfo(content, filePath, category);
    
    if (apiInfo && Object.keys(apiInfo).length > 0) {
      this.apiData[category].push({
        filePath: relativePath,
        fullPath: filePath,
        ...apiInfo
      });
    }
  }

  /**
   * Categorize file based on its path
   * 
   * @param {string} relativePath - Relative path of the file
   * @returns {string} Category name
   */
  categorizeFile(relativePath) {
    if (relativePath.includes('/services/')) return 'services';
    if (relativePath.includes('/components/')) return 'components';
    if (relativePath.includes('/types/')) return 'types';
    if (relativePath.includes('/hooks/')) return 'hooks';
    if (relativePath.includes('/utils/')) return 'utilities';
    return 'utilities';
  }

  /**
   * Extract API information from file content
   * 
   * @param {string} content - File content
   * @param {string} filePath - File path
   * @param {string} category - File category
   * @returns {Object} Extracted API information
   */
  extractAPIInfo(content, filePath, category) {
    const apiInfo = {
      name: path.basename(filePath, path.extname(filePath)),
      description: '',
      exports: [],
      classes: [],
      functions: [],
      interfaces: [],
      types: [],
      constants: []
    };

    // Extract file-level JSDoc comment
    const fileDocMatch = content.match(/\/\*\*\s*\n\s*\*\s*@fileoverview\s+(.*?)\n[\s\S]*?\*\//);
    if (fileDocMatch) {
      apiInfo.description = this.parseJSDocComment(fileDocMatch[0]);
    }

    // Extract classes
    const classMatches = content.matchAll(/\/\*\*[\s\S]*?\*\/\s*export\s+class\s+(\w+)[\s\S]*?{/g);
    for (const match of classMatches) {
      const className = match[1];
      const classDoc = this.parseJSDocComment(match[0]);
      const methods = this.extractClassMethods(content, className);
      
      apiInfo.classes.push({
        name: className,
        description: classDoc.description,
        methods,
        examples: classDoc.examples || []
      });
    }

    // Extract functions
    const functionMatches = content.matchAll(/\/\*\*[\s\S]*?\*\/\s*export\s+(?:async\s+)?function\s+(\w+)/g);
    for (const match of functionMatches) {
      const functionName = match[1];
      const functionDoc = this.parseJSDocComment(match[0]);
      
      apiInfo.functions.push({
        name: functionName,
        description: functionDoc.description,
        parameters: functionDoc.params || [],
        returns: functionDoc.returns,
        examples: functionDoc.examples || []
      });
    }

    // Extract interfaces
    const interfaceMatches = content.matchAll(/\/\*\*[\s\S]*?\*\/\s*export\s+interface\s+(\w+)/g);
    for (const match of interfaceMatches) {
      const interfaceName = match[1];
      const interfaceDoc = this.parseJSDocComment(match[0]);
      
      apiInfo.interfaces.push({
        name: interfaceName,
        description: interfaceDoc.description,
        properties: this.extractInterfaceProperties(content, interfaceName)
      });
    }

    // Extract type aliases
    const typeMatches = content.matchAll(/\/\*\*[\s\S]*?\*\/\s*export\s+type\s+(\w+)/g);
    for (const match of typeMatches) {
      const typeName = match[1];
      const typeDoc = this.parseJSDocComment(match[0]);
      
      apiInfo.types.push({
        name: typeName,
        description: typeDoc.description
      });
    }

    return apiInfo;
  }

  /**
   * Parse JSDoc comment block
   * 
   * @param {string} comment - JSDoc comment block
   * @returns {Object} Parsed JSDoc information
   */
  parseJSDocComment(comment) {
    const result = {
      description: '',
      params: [],
      returns: null,
      examples: [],
      author: null,
      version: null,
      since: null
    };

    // Extract description
    const descMatch = comment.match(/\/\*\*\s*\n\s*\*\s*([^@\n].*?)(?:\n\s*\*\s*@|\n\s*\*\/)/s);
    if (descMatch) {
      result.description = descMatch[1].replace(/\n\s*\*\s*/g, ' ').trim();
    }

    // Extract @param tags
    const paramMatches = comment.matchAll(/@param\s+{([^}]+)}\s+(\w+)\s*-?\s*(.*?)(?=\n\s*\*\s*@|\n\s*\*\/)/gs);
    for (const match of paramMatches) {
      result.params.push({
        type: match[1],
        name: match[2],
        description: match[3].replace(/\n\s*\*\s*/g, ' ').trim()
      });
    }

    // Extract @returns tag
    const returnsMatch = comment.match(/@returns?\s+{([^}]+)}\s*(.*?)(?=\n\s*\*\s*@|\n\s*\*\/)/s);
    if (returnsMatch) {
      result.returns = {
        type: returnsMatch[1],
        description: returnsMatch[2].replace(/\n\s*\*\s*/g, ' ').trim()
      };
    }

    // Extract @example tags
    const exampleMatches = comment.matchAll(/@example\s*\n\s*\*\s*([\s\S]*?)(?=\n\s*\*\s*@|\n\s*\*\/)/g);
    for (const match of exampleMatches) {
      result.examples.push(match[1].replace(/\n\s*\*\s*/g, '\n').trim());
    }

    // Extract other tags
    const authorMatch = comment.match(/@author\s+(.*?)(?=\n\s*\*\s*@|\n\s*\*\/)/);
    if (authorMatch) result.author = authorMatch[1].trim();

    const versionMatch = comment.match(/@version\s+(.*?)(?=\n\s*\*\s*@|\n\s*\*\/)/);
    if (versionMatch) result.version = versionMatch[1].trim();

    const sinceMatch = comment.match(/@since\s+(.*?)(?=\n\s*\*\s*@|\n\s*\*\/)/);
    if (sinceMatch) result.since = sinceMatch[1].trim();

    return result;
  }

  /**
   * Extract methods from a class
   * 
   * @param {string} content - File content
   * @param {string} className - Name of the class
   * @returns {Array} Array of method information
   */
  extractClassMethods(content, className) {
    const methods = [];
    
    // Find class definition
    const classRegex = new RegExp(`class\\s+${className}[\\s\\S]*?{([\\s\\S]*?)(?=\\n\\s*}\\s*$|\\nexport)`, 'm');
    const classMatch = content.match(classRegex);
    
    if (classMatch) {
      const classBody = classMatch[1];
      
      // Extract methods with JSDoc
      const methodMatches = classBody.matchAll(/\/\*\*[\s\S]*?\*\/\s*(?:async\s+)?(\w+)\s*\(/g);
      for (const match of methodMatches) {
        const methodName = match[1];
        if (methodName !== 'constructor') {
          const methodDoc = this.parseJSDocComment(match[0]);
          methods.push({
            name: methodName,
            description: methodDoc.description,
            parameters: methodDoc.params || [],
            returns: methodDoc.returns,
            examples: methodDoc.examples || []
          });
        }
      }
    }
    
    return methods;
  }

  /**
   * Extract properties from an interface
   * 
   * @param {string} content - File content
   * @param {string} interfaceName - Name of the interface
   * @returns {Array} Array of property information
   */
  extractInterfaceProperties(content, interfaceName) {
    const properties = [];
    
    // Find interface definition
    const interfaceRegex = new RegExp(`interface\\s+${interfaceName}[\\s\\S]*?{([\\s\\S]*?)}`, 'm');
    const interfaceMatch = content.match(interfaceRegex);
    
    if (interfaceMatch) {
      const interfaceBody = interfaceMatch[1];
      
      // Extract properties with comments
      const propertyMatches = interfaceBody.matchAll(/\/\*\*\s*(.*?)\s*\*\/\s*(\w+)(?:\?)?\s*:\s*([^;]+);/g);
      for (const match of propertyMatches) {
        properties.push({
          name: match[2],
          type: match[3].trim(),
          description: match[1].trim(),
          optional: match[0].includes('?')
        });
      }
    }
    
    return properties;
  }

  /**
   * Generate documentation in all configured formats
   * 
   * @returns {Promise<void>}
   */
  async generateDocumentation() {
    console.log('📝 Generating documentation...');
    
    for (const format of this.config.formats) {
      switch (format) {
        case 'html':
          await this.generateHTMLDocs();
          break;
        case 'markdown':
          await this.generateMarkdownDocs();
          break;
        case 'json':
          await this.generateJSONDocs();
          break;
      }
    }
  }

  /**
   * Generate HTML documentation
   * 
   * @returns {Promise<void>}
   */
  async generateHTMLDocs() {
    const htmlDir = path.join(this.config.outputDir, 'html');
    
    // Generate main index page
    const indexHTML = this.generateHTMLIndex();
    fs.writeFileSync(path.join(htmlDir, 'index.html'), indexHTML);
    
    // Generate category pages
    for (const [category, items] of Object.entries(this.apiData)) {
      if (items.length > 0) {
        const categoryHTML = this.generateHTMLCategory(category, items);
        fs.writeFileSync(path.join(htmlDir, `${category}.html`), categoryHTML);
      }
    }
    
    // Copy CSS and assets
    this.copyHTMLAssets(htmlDir);
  }

  /**
   * Generate HTML index page
   * 
   * @returns {string} HTML content
   */
  generateHTMLIndex() {
    const stats = Object.entries(this.apiData).map(([category, items]) => ({
      category,
      count: items.length
    }));

    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Scholar API Documentation</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>AI Scholar API Documentation</h1>
        <p>Comprehensive API documentation for the AI Scholar RAG chatbot</p>
    </header>
    
    <main>
        <section class="overview">
            <h2>API Overview</h2>
            <div class="stats">
                ${stats.map(stat => `
                    <div class="stat-card">
                        <h3>${stat.count}</h3>
                        <p><a href="${stat.category}.html">${stat.category.charAt(0).toUpperCase() + stat.category.slice(1)}</a></p>
                    </div>
                `).join('')}
            </div>
        </section>
        
        <section class="categories">
            <h2>API Categories</h2>
            <div class="category-grid">
                ${Object.entries(this.apiData).map(([category, items]) => `
                    <div class="category-card">
                        <h3><a href="${category}.html">${category.charAt(0).toUpperCase() + category.slice(1)}</a></h3>
                        <p>${items.length} items</p>
                        <ul>
                            ${items.slice(0, 5).map(item => `<li>${item.name}</li>`).join('')}
                            ${items.length > 5 ? '<li>...</li>' : ''}
                        </ul>
                    </div>
                `).join('')}
            </div>
        </section>
    </main>
    
    <footer>
        <p>Generated on ${new Date().toISOString()}</p>
    </footer>
</body>
</html>`;
  }

  /**
   * Generate Markdown documentation
   * 
   * @returns {Promise<void>}
   */
  async generateMarkdownDocs() {
    const markdownDir = path.join(this.config.outputDir, 'markdown');
    
    // Generate main README
    const readmeContent = this.generateMarkdownIndex();
    fs.writeFileSync(path.join(markdownDir, 'README.md'), readmeContent);
    
    // Generate category files
    for (const [category, items] of Object.entries(this.apiData)) {
      if (items.length > 0) {
        const categoryContent = this.generateMarkdownCategory(category, items);
        fs.writeFileSync(path.join(markdownDir, `${category}.md`), categoryContent);
      }
    }
  }

  /**
   * Generate Markdown index
   * 
   * @returns {string} Markdown content
   */
  generateMarkdownIndex() {
    return `# AI Scholar API Documentation

Comprehensive API documentation for the AI Scholar RAG chatbot application.

## Overview

This documentation covers all public APIs, services, components, and utilities available in the AI Scholar application.

## API Categories

${Object.entries(this.apiData).map(([category, items]) => `
### [${category.charAt(0).toUpperCase() + category.slice(1)}](${category}.md)

${items.length} items available

${items.slice(0, 3).map(item => `- **${item.name}**: ${item.description || 'No description available'}`).join('\n')}
${items.length > 3 ? '- ...' : ''}
`).join('\n')}

## Quick Start

\`\`\`typescript
// Import services
import { analyticsService } from './services/analyticsService';
import { chartService } from './services/chartService';

// Use services
analyticsService.logQuery(queryData);
chartService.renderChart('chartId', config);
\`\`\`

## Documentation Format

Each API item includes:

- **Description**: What the API does
- **Parameters**: Input parameters with types
- **Returns**: Return value type and description
- **Examples**: Code examples showing usage
- **Notes**: Additional information and considerations

## Generated

This documentation was automatically generated on ${new Date().toISOString()}.
`;
  }

  /**
   * Generate JSON documentation
   * 
   * @returns {Promise<void>}
   */
  async generateJSONDocs() {
    const jsonDir = path.join(this.config.outputDir, 'json');
    
    // Write complete API data
    fs.writeFileSync(
      path.join(jsonDir, 'api-complete.json'),
      JSON.stringify(this.apiData, null, 2)
    );
    
    // Write individual category files
    for (const [category, items] of Object.entries(this.apiData)) {
      if (items.length > 0) {
        fs.writeFileSync(
          path.join(jsonDir, `${category}.json`),
          JSON.stringify(items, null, 2)
        );
      }
    }
    
    // Write summary file
    const summary = {
      generatedAt: new Date().toISOString(),
      totalFiles: this.sourceFiles.length,
      categories: Object.entries(this.apiData).map(([category, items]) => ({
        name: category,
        count: items.length
      }))
    };
    
    fs.writeFileSync(
      path.join(jsonDir, 'summary.json'),
      JSON.stringify(summary, null, 2)
    );
  }

  /**
   * Generate index files for easy navigation
   * 
   * @returns {Promise<void>}
   */
  async generateIndexFiles() {
    // Generate TypeScript declaration file for API types
    const declarationContent = this.generateTypeDeclarations();
    fs.writeFileSync(
      path.join(this.config.outputDir, 'api-types.d.ts'),
      declarationContent
    );
    
    console.log('📋 Generated index files');
  }

  /**
   * Generate TypeScript declarations for documented APIs
   * 
   * @returns {string} TypeScript declaration content
   */
  generateTypeDeclarations() {
    let content = `/**
 * Auto-generated API type declarations
 * Generated on ${new Date().toISOString()}
 */

`;

    // Generate interface declarations
    for (const category of Object.values(this.apiData)) {
      for (const item of category) {
        if (item.interfaces) {
          for (const iface of item.interfaces) {
            content += `export interface ${iface.name} {\n`;
            for (const prop of iface.properties || []) {
              content += `  /** ${prop.description} */\n`;
              content += `  ${prop.name}${prop.optional ? '?' : ''}: ${prop.type};\n`;
            }
            content += `}\n\n`;
          }
        }
      }
    }

    return content;
  }

  /**
   * Copy HTML assets (CSS, JS, images)
   * 
   * @param {string} htmlDir - HTML output directory
   */
  copyHTMLAssets(htmlDir) {
    const cssContent = `
/* API Documentation Styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
  color: #333;
  background-color: #f8f9fa;
}

header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem 0;
  text-align: center;
}

header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin: 2rem 0;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  text-align: center;
}

.stat-card h3 {
  font-size: 2rem;
  color: #667eea;
  margin-bottom: 0.5rem;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}

.category-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.category-card h3 {
  color: #667eea;
  margin-bottom: 1rem;
}

.category-card ul {
  list-style: none;
}

.category-card li {
  padding: 0.25rem 0;
  color: #666;
}

footer {
  text-align: center;
  padding: 2rem;
  color: #666;
  border-top: 1px solid #eee;
  margin-top: 3rem;
}

a {
  color: #667eea;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
`;

    fs.writeFileSync(path.join(htmlDir, 'styles.css'), cssContent);
  }
}

// CLI interface
if (require.main === module) {
  const generator = new APIDocumentationGenerator();
  generator.generate().catch(console.error);
}

module.exports = { APIDocumentationGenerator };