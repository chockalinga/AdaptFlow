export interface WorkflowMode {
  type: 'framework' | 'workflow_pattern';
}

export interface WorkflowPattern {
  id: string;
  name: string;
  description: string;
  type: string;
}

export interface WorkflowPatternExample {
  scenario: string;
  implementation: string;
}

export interface WorkflowPattern {
  id: string;
  name: string;
  description: string;
  type: string;
  detailedDescription?: string;
  examples?: WorkflowPatternExample[];
}

export const WORKFLOW_PATTERNS: WorkflowPattern[] = [
  {
    id: 'evaluator_optimizer',
    name: 'Evaluator-Optimizer',
    description: 'Self-improving system with evaluation and feedback loops',
    type: 'evaluator_optimizer',
    detailedDescription: 'A pattern that enables agents to evaluate their own output and improve performance through feedback loops. The system generates solutions, evaluates them against defined criteria, and iteratively optimizes based on the evaluation results.',
    examples: [
      {
        scenario: 'Code Generation Quality Control',
        implementation: 'An agent generates code, evaluates it for performance and best practices, then improves the code based on evaluation feedback.'
      },
      {
        scenario: 'Content Writing Refinement',
        implementation: 'System generates content, evaluates readability and engagement metrics, then refines the content through multiple iterations.'
      }
    ]
  },
  {
    id: 'prompt_chain',
    name: 'Prompt Chain',
    description: 'Break down complex tasks into sequential steps with validation gates',
    type: 'prompt_chain',
    detailedDescription: 'A sequential pattern where the output of one LLM call becomes input for the next, creating a chain of reasoning or processing steps. Each step can include validation gates to ensure quality before proceeding.',
    examples: [
      {
        scenario: 'Document Analysis Pipeline',
        implementation: 'Chain of steps: 1) Extract key information 2) Summarize findings 3) Generate recommendations - each with quality validation.'
      },
      {
        scenario: 'Code Review Process',
        implementation: 'Sequential review steps: 1) Style check 2) Logic analysis 3) Security review 4) Performance optimization suggestions.'
      }
    ]
  },
  {
    id: 'routing',
    name: 'Routing',
    description: 'Route tasks to specialized handlers based on content analysis',
    type: 'routing',
    detailedDescription: 'Dynamic decision-making pattern that directs tasks to appropriate handlers based on content or requirements. Includes a classifier component that analyzes input and routes to specialized processors.',
    examples: [
      {
        scenario: 'Customer Support Triage',
        implementation: 'Analyzes customer queries and routes to appropriate department: technical support, billing, or general inquiries.'
      },
      {
        scenario: 'Code Issue Classification',
        implementation: 'Routes code problems to specialized handlers for bugs, feature requests, or documentation issues.'
      }
    ]
  },
  {
    id: 'parallelization',
    name: 'Parallelization',
    description: 'Process multiple tasks concurrently for improved efficiency',
    type: 'parallelization',
    detailedDescription: 'Pattern for executing multiple LLM operations concurrently to improve performance. Includes strategies for task distribution, parallel processing, and result aggregation.',
    examples: [
      {
        scenario: 'Batch Document Processing',
        implementation: 'Process multiple documents simultaneously, with parallel workers handling different sections or documents.'
      },
      {
        scenario: 'Multi-Version Generation',
        implementation: 'Generate multiple versions of content in parallel, then aggregate and select the best results.'
      }
    ]
  }
];
