// Prompt Template System for Flexible Response Styles
export interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  category: 'reasoning' | 'qa' | 'dialogue' | 'analysis' | 'creative';
  template: string;
  variables: string[];
  examples: PromptExample[];
}

export interface PromptExample {
  input: Record<string, string>;
  expectedOutput: string;
}

export class PromptTemplateService {
  private templates: Map<string, PromptTemplate> = new Map();

  constructor() {
    this.initializeDefaultTemplates();
  }

  /**
   * Get all available templates
   */
  getTemplates(): PromptTemplate[] {
    return Array.from(this.templates.values());
  }

  /**
   * Get template by ID
   */
  getTemplate(id: string): PromptTemplate | null {
    return this.templates.get(id) || null;
  }

  /**
   * Apply template with variables
   */
  applyTemplate(templateId: string, variables: Record<string, string>): string {
    const template = this.templates.get(templateId);
    if (!template) {
      throw new Error(`Template ${templateId} not found`);
    }

    let prompt = template.template;
    
    // Replace variables
    template.variables.forEach(variable => {
      const value = variables[variable] || '';
      prompt = prompt.replace(new RegExp(`{{${variable}}}`, 'g'), value);
    });

    return prompt;
  }

  /**
   * Create custom template
   */
  createTemplate(template: Omit<PromptTemplate, 'id'>): PromptTemplate {
    const id = `custom_${Date.now()}`;
    const newTemplate: PromptTemplate = { ...template, id };
    this.templates.set(id, newTemplate);
    return newTemplate;
  }

  /**
   * Initialize default templates
   */
  private initializeDefaultTemplates(): void {
    // Chain of Thought Template
    this.templates.set('chain_of_thought', {
      id: 'chain_of_thought',
      name: 'Chain of Thought Reasoning',
      description: 'Step-by-step reasoning for complex problems',
      category: 'reasoning',
      template: `Let me think through this step by step.

Context: {{context}}

Question: {{question}}

Let me break this down:

Step 1: Understanding the question
{{question}} - This is asking about...

Step 2: Analyzing the available information
From the context, I can see that...

Step 3: Reasoning through the problem
Based on the information, I need to consider...

Step 4: Drawing conclusions
Therefore, the answer is...

Final Answer: {{answer}}`,
      variables: ['context', 'question', 'answer'],
      examples: [{
        input: {
          context: 'Machine learning research papers',
          question: 'What are the main differences between supervised and unsupervised learning?',
          answer: 'To be filled by the model'
        },
        expectedOutput: 'Step-by-step analysis of supervised vs unsupervised learning'
      }]
    });

    // Direct Q&A Template
    this.templates.set('direct_qa', {
      id: 'direct_qa',
      name: 'Direct Question & Answer',
      description: 'Concise, direct answers to questions',
      category: 'qa',
      template: `Based on the provided context, here is a direct answer to your question:

Context: {{context}}

Question: {{question}}

Answer: {{answer}}

Sources: {{sources}}`,
      variables: ['context', 'question', 'answer', 'sources'],
      examples: [{
        input: {
          context: 'Technical documentation',
          question: 'How do I install the software?',
          answer: 'To be filled by the model',
          sources: 'Installation guide, page 3'
        },
        expectedOutput: 'Clear installation instructions'
      }]
    });

    // Socratic Dialogue Template
    this.templates.set('socratic_dialogue', {
      id: 'socratic_dialogue',
      name: 'Socratic Dialogue',
      description: 'Guided learning through questions',
      category: 'dialogue',
      template: `I'll help you explore this topic through guided questions.

Your question: {{question}}

Let me ask you some questions to help you think through this:

1. What do you already know about {{topic}}?

2. Based on the context: {{context}}
   What patterns do you notice?

3. How might this relate to {{related_concept}}?

4. What questions does this raise for you?

Let's explore this together. What are your thoughts on the first question?`,
      variables: ['question', 'topic', 'context', 'related_concept'],
      examples: [{
        input: {
          question: 'How do neural networks learn?',
          topic: 'neural networks',
          context: 'Deep learning research',
          related_concept: 'human learning'
        },
        expectedOutput: 'Guided exploration of neural network learning'
      }]
    });

    // Research Analysis Template
    this.templates.set('research_analysis', {
      id: 'research_analysis',
      name: 'Research Analysis',
      description: 'Academic-style analysis with citations',
      category: 'analysis',
      template: `# Research Analysis: {{topic}}

## Abstract
{{abstract}}

## Key Findings
Based on the analysis of {{source_count}} sources:

{{findings}}

## Methodology
The analysis employed {{methodology}} to examine {{research_question}}.

## Results
{{results}}

## Discussion
{{discussion}}

## Limitations
{{limitations}}

## Conclusions
{{conclusions}}

## References
{{references}}`,
      variables: ['topic', 'abstract', 'source_count', 'findings', 'methodology', 'research_question', 'results', 'discussion', 'limitations', 'conclusions', 'references'],
      examples: [{
        input: {
          topic: 'Transformer Architecture in NLP',
          abstract: 'Analysis of transformer models',
          source_count: '15',
          findings: 'Key architectural innovations',
          methodology: 'Systematic literature review',
          research_question: 'How do transformers improve NLP tasks?',
          results: 'Significant improvements in performance',
          discussion: 'Implications for future research',
          limitations: 'Limited to English language papers',
          conclusions: 'Transformers represent a paradigm shift',
          references: 'Vaswani et al. (2017), etc.'
        },
        expectedOutput: 'Comprehensive research analysis'
      }]
    });

    // Creative Exploration Template
    this.templates.set('creative_exploration', {
      id: 'creative_exploration',
      name: 'Creative Exploration',
      description: 'Creative and imaginative responses',
      category: 'creative',
      template: `Let's explore {{topic}} from a creative perspective!

🎨 Imagine if {{scenario}}...

🔍 Looking at this from different angles:
- The traditional view: {{traditional_view}}
- A fresh perspective: {{fresh_perspective}}
- An unexpected connection: {{unexpected_connection}}

💡 Creative insights:
{{creative_insights}}

🌟 What if we considered {{what_if_scenario}}?

This opens up fascinating possibilities for {{future_implications}}.

What creative connections do you see?`,
      variables: ['topic', 'scenario', 'traditional_view', 'fresh_perspective', 'unexpected_connection', 'creative_insights', 'what_if_scenario', 'future_implications'],
      examples: [{
        input: {
          topic: 'artificial intelligence',
          scenario: 'AI could learn like children do',
          traditional_view: 'AI as computational systems',
          fresh_perspective: 'AI as curious learners',
          unexpected_connection: 'AI and artistic creativity',
          creative_insights: 'Learning through play and exploration',
          what_if_scenario: 'AI developed emotional intelligence',
          future_implications: 'human-AI collaboration'
        },
        expectedOutput: 'Creative exploration of AI concepts'
      }]
    });

    // Comparative Analysis Template
    this.templates.set('comparative_analysis', {
      id: 'comparative_analysis',
      name: 'Comparative Analysis',
      description: 'Side-by-side comparison of concepts',
      category: 'analysis',
      template: `# Comparative Analysis: {{concept_a}} vs {{concept_b}}

## Overview
This analysis compares {{concept_a}} and {{concept_b}} across multiple dimensions.

## Key Similarities
{{similarities}}

## Key Differences
| Aspect | {{concept_a}} | {{concept_b}} |
|--------|---------------|---------------|
{{comparison_table}}

## Detailed Analysis

### {{concept_a}}
**Strengths:** {{strengths_a}}
**Weaknesses:** {{weaknesses_a}}
**Use Cases:** {{use_cases_a}}

### {{concept_b}}
**Strengths:** {{strengths_b}}
**Weaknesses:** {{weaknesses_b}}
**Use Cases:** {{use_cases_b}}

## Conclusion
{{conclusion}}

## Recommendations
{{recommendations}}`,
      variables: ['concept_a', 'concept_b', 'similarities', 'comparison_table', 'strengths_a', 'weaknesses_a', 'use_cases_a', 'strengths_b', 'weaknesses_b', 'use_cases_b', 'conclusion', 'recommendations'],
      examples: [{
        input: {
          concept_a: 'Supervised Learning',
          concept_b: 'Unsupervised Learning',
          similarities: 'Both are machine learning paradigms',
          comparison_table: '| Data Requirements | Labeled data | Unlabeled data |',
          strengths_a: 'Clear objectives, measurable performance',
          weaknesses_a: 'Requires labeled data',
          use_cases_a: 'Classification, regression',
          strengths_b: 'No labeling required, discovers hidden patterns',
          weaknesses_b: 'Harder to evaluate',
          use_cases_b: 'Clustering, dimensionality reduction',
          conclusion: 'Both approaches have distinct advantages',
          recommendations: 'Choose based on data availability and objectives'
        },
        expectedOutput: 'Comprehensive comparison of learning paradigms'
      }]
    });

    // Tutorial Template
    this.templates.set('tutorial', {
      id: 'tutorial',
      name: 'Step-by-Step Tutorial',
      description: 'Educational tutorial format',
      category: 'qa',
      template: `# {{title}}

## What You'll Learn
{{learning_objectives}}

## Prerequisites
{{prerequisites}}

## Step-by-Step Guide

{{steps}}

## Common Issues & Solutions
{{troubleshooting}}

## Next Steps
{{next_steps}}

## Additional Resources
{{resources}}`,
      variables: ['title', 'learning_objectives', 'prerequisites', 'steps', 'troubleshooting', 'next_steps', 'resources'],
      examples: [{
        input: {
          title: 'Getting Started with Machine Learning',
          learning_objectives: 'Understand basic ML concepts',
          prerequisites: 'Basic programming knowledge',
          steps: 'Step 1: Data collection...',
          troubleshooting: 'Common error: overfitting',
          next_steps: 'Explore deep learning',
          resources: 'Books, courses, papers'
        },
        expectedOutput: 'Structured learning tutorial'
      }]
    });
  }
}

export const promptTemplateService = new PromptTemplateService();