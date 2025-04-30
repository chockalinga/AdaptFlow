import { LATSConfig } from './lats';

export interface LangGraphNode {
  name: string;
  description: string;
  agent: string;
}

export interface LangGraphEdge {
  source: string;
  target: string;
  condition?: string;
}

export interface LangGraphConfig {
  agents: Array<{
    name: string;
    role: string;
    goal: string;
    tools: string[];
    model_id: string;
  }>;
  nodes: LangGraphNode[];
  edges: LangGraphEdge[];
}

export interface ReactConfig {
  agents: Array<{
    name: string;
    role: string;
    goal: string;
    tools: string[];
    model_id: string;
  }>;
  tools: Array<{
    name: string;
    description: string;
    parameters: Record<string, string>;
  }>;
  examples?: Array<{
    query: string;
    thought: string;
    action: string;
    observation: string;
    final_answer: string;
  }>;
}

export interface PromptChainStep {
  name: string;
  description: string;
  prompt_template: string;
  output_key: string;
  has_gate: boolean;
  gate_condition?: string;
}

export interface RouteHandler {
  name: string;
  description: string;
  prompt_template: string;
  input_variables: string[];
  output_format: {
    type: string;
    properties: Record<string, any>;
  };
}

export interface RoutingStep {
  name: string;
  description: string;
  classifier_prompt: string;
  output_key: string;
  input_variables: string[];
  handlers: RouteHandler[];
  output_format: {
    type: string;
    properties: Record<string, any>;
  };
}

export interface RoutingConfig {
  workflow_type: 'routing';
  description: string;
  steps: RoutingStep[];
  input_variables: string[];
  output_variable: string;
}

export interface ParallelTask {
  name: string;
  description: string;
  prompt_template: string;
  input_variables: string[];
  output_format: {
    type: string;
    properties: Record<string, any>;
  };
}

export interface ParallelizationStep {
  name: string;
  description: string;
  execution_mode: 'sectioning' | 'voting';
  tasks: ParallelTask[];
  max_workers: number;
  aggregation_strategy: {
    type: 'merge' | 'vote' | 'consensus';
    threshold?: number;
    combine_method?: string;
  };
  output_key: string;
  input_variables: string[];
  output_format: {
    type: string;
    properties: Record<string, any>;
  };
}

export interface ParallelizationConfig {
  workflow_type: 'parallelization';
  description: string;
  steps: ParallelizationStep[];
  input_variables: string[];
  output_variable: string;
}

export interface PromptChainConfig {
  workflow_type: 'prompt_chain';
  description: string;
  steps: PromptChainStep[];
  input_variables: string[];
  output_variable: string;
}

export interface OrchestratorTask {
  type: string;
  description: string;
  input_variables: string[];
  output_format: {
    type: string;
    properties: Record<string, any>;
  };
}

export interface OrchestratorConfig {
  workflow_type: 'orchestrator';
  description: string;
  tasks: OrchestratorTask[];
  orchestrator_config: {
    orchestrator_prompt: string;
    worker_prompt: string;
    max_workers: number;
    retry_attempts: number;
  };
  worker_configs: Array<{
    type: string;
    description: string;
    prompt_template: string;
    output_format: {
      type: string;
      properties: Record<string, any>;
    };
  }>;
  input_variables: string[];
  output_variable: string;
}

export interface EvaluationCriterion {
  name: string;
  description: string;
  weight: number;
  required: boolean;
}

export interface EvaluatorOptimizerConfig {
  workflow_type: 'evaluator_optimizer';
  description: string;
  task_description: string;
  input_variables: string[];
  output_variable: string;
  evaluation_criteria: EvaluationCriterion[];
  max_iterations: number;
  success_threshold: number;
  generator_prompt: string;
  evaluator_prompt: string;
  output_format: {
    type: string;
    properties: Record<string, any>;
  };
  evaluation_format: {
    type: string;
    properties: Record<string, any>;
  };
}

export type FrameworkConfig = 
  | LATSConfig 
  | LangGraphConfig 
  | ReactConfig 
  | PromptChainConfig 
  | RoutingConfig 
  | ParallelizationConfig 
  | OrchestratorConfig 
  | EvaluatorOptimizerConfig;
