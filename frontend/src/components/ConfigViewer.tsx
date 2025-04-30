import React from 'react';
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  Box,
  LinearProgress,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { 
  FrameworkConfig, 
  LangGraphConfig, 
  ReactConfig,
  PromptChainConfig,
  PromptChainStep,
  RoutingConfig,
  RoutingStep,
  RouteHandler,
  ParallelizationConfig,
  ParallelizationStep,
  ParallelTask,
  OrchestratorConfig,
  EvaluatorOptimizerConfig,
  EvaluationCriterion
} from '../types/frameworks';
import { LATSConfig } from '../types/lats';

interface ConfigViewerProps {
  config: FrameworkConfig;
  framework: string;
}

interface AgentConfig {
  name: string;
  role: string;
  goal: string;
  tools: string[];
}

const isLATSConfig = (config: FrameworkConfig): config is LATSConfig => {
  return 'workflow' in config;
};

const isLangGraphConfig = (config: FrameworkConfig): config is LangGraphConfig => {
  return 'nodes' in config && 'edges' in config;
};

const isReactConfig = (config: FrameworkConfig): config is ReactConfig => {
  return !('workflow' in config) && !('nodes' in config) && 'tools' in config;
};

const isPromptChainConfig = (config: FrameworkConfig): config is PromptChainConfig => {
  return 'workflow_type' in config && config.workflow_type === 'prompt_chain';
};

const isRoutingConfig = (config: FrameworkConfig): config is RoutingConfig => {
  return 'workflow_type' in config && config.workflow_type === 'routing';
};

const isParallelizationConfig = (config: FrameworkConfig): config is ParallelizationConfig => {
  return 'workflow_type' in config && config.workflow_type === 'parallelization';
};

const isOrchestratorConfig = (config: FrameworkConfig): config is OrchestratorConfig => {
  return 'workflow_type' in config && config.workflow_type === 'orchestrator';
};

const isEvaluatorOptimizerConfig = (config: FrameworkConfig): config is EvaluatorOptimizerConfig => {
  return 'workflow_type' in config && config.workflow_type === 'evaluator_optimizer';
};

const hasAgents = (config: FrameworkConfig): config is (LangGraphConfig | ReactConfig | LATSConfig) => {
  return 'agents' in config && Array.isArray(config.agents);
};

const ConfigViewer: React.FC<ConfigViewerProps> = ({ config, framework }) => {
  const renderAgents = (): React.ReactElement | null => {
    if (!hasAgents(config) || isPromptChainConfig(config)) return null;
    return (
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">🤖 Agents</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            {config.agents.map((agent: AgentConfig, index: number) => (
              <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {agent.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Role: {agent.role}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Goal: {agent.goal}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  {agent.tools.map((tool: string, toolIndex: number) => (
                    <Chip
                      key={toolIndex}
                      label={tool}
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))}
                </Box>
              </ListItem>
            ))}
          </List>
        </AccordionDetails>
      </Accordion>
    );
  };

  const renderPromptChain = (): React.ReactElement | null => {
    if (!isPromptChainConfig(config)) return null;
    return (
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">⛓️ Prompt Chain</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="subtitle1" gutterBottom>
            Description: {config.description}
          </Typography>
          
          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Input Variables:
          </Typography>
          <Box sx={{ mb: 2 }}>
            {config.input_variables.map((variable: string, index: number) => (
              <Chip
                key={index}
                label={variable}
                size="small"
                sx={{ mr: 1, mb: 1 }}
              />
            ))}
          </Box>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Steps:
          </Typography>
          <List>
            {config.steps.map((step: PromptChainStep, index: number) => (
              <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {index + 1}. {step.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {step.description}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Output: {step.output_key}
                </Typography>
                {step.has_gate && (
                  <Box sx={{ mt: 1 }}>
                    <Chip
                      label={`Validation: ${step.gate_condition}`}
                      color="primary"
                      size="small"
                    />
                  </Box>
                )}
              </ListItem>
            ))}
          </List>

          <Typography variant="subtitle2" sx={{ mt: 2 }}>
            Output Variable: {config.output_variable}
          </Typography>
        </AccordionDetails>
      </Accordion>
    );
  };

  const renderTools = (): React.ReactElement | null => {
    if (!isReactConfig(config) && !isLATSConfig(config)) return null;
    if (!config.tools) return null;
    return (
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">🔧 Tools</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            {config.tools.map((tool, index) => (
              <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {tool.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {tool.description}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  {Object.entries(tool.parameters).map(([param, desc]) => (
                    <Chip
                      key={param}
                      label={`${param}: ${desc}`}
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))}
                </Box>
              </ListItem>
            ))}
          </List>
        </AccordionDetails>
      </Accordion>
    );
  };

  const renderNodes = (): React.ReactElement | null => {
    if (!isLangGraphConfig(config)) return null;
    return (
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">📍 Nodes</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            {config.nodes.map((node, index) => (
              <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {node.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Description: {node.description}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Agent: {node.agent}
                </Typography>
              </ListItem>
            ))}
          </List>
        </AccordionDetails>
      </Accordion>
    );
  };

  const renderEdges = (): React.ReactElement | null => {
    if (!isLangGraphConfig(config)) return null;
    return (
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">🔗 Edges</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            {config.edges.map((edge, index) => (
              <ListItem key={index}>
                <ListItemText
                  primary={`${edge.source} → ${edge.target}`}
                  secondary={edge.condition ? `Condition: ${edge.condition}` : null}
                />
              </ListItem>
            ))}
          </List>
        </AccordionDetails>
      </Accordion>
    );
  };

  const renderWorkflow = (): React.ReactElement | null => {
    if (!isLATSConfig(config)) return null;
    return (
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">⚙️ Workflow</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <ListItem>
              <Box sx={{ width: '100%' }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  Phases
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  {config.workflow.phases.map((phase, index) => (
                    <Chip
                      key={index}
                      label={phase}
                      color="primary"
                      variant="outlined"
                    />
                  ))}
                </Box>
                <Typography variant="subtitle1" fontWeight="bold">
                  Iterations
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Maximum iterations: {config.workflow.iterations}
                </Typography>
                <Typography variant="subtitle1" fontWeight="bold">
                  Consensus Threshold
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <LinearProgress
                    variant="determinate"
                    value={config.workflow.consensus_threshold * 100}
                    sx={{ flexGrow: 1 }}
                  />
                  <Typography variant="body2">
                    {(config.workflow.consensus_threshold * 100).toFixed(0)}%
                  </Typography>
                </Box>
              </Box>
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>
    );
  };

  const renderRouting = (): React.ReactElement | null => {
    if (!isRoutingConfig(config)) return null;
    return (
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">🔀 Routing Workflow</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="subtitle1" gutterBottom>
            Description: {config.description}
          </Typography>
          
          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Input Variables:
          </Typography>
          <Box sx={{ mb: 2 }}>
            {config.input_variables.map((variable: string, index: number) => (
              <Chip
                key={index}
                label={variable}
                size="small"
                sx={{ mr: 1, mb: 1 }}
              />
            ))}
          </Box>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Steps:
          </Typography>
          <List>
            {config.steps.map((step: RoutingStep, index: number) => (
              <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {index + 1}. {step.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {step.description}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Output: {step.output_key}
                </Typography>
                
                <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                  Handlers:
                </Typography>
                <List sx={{ pl: 2 }}>
                  {step.handlers.map((handler: RouteHandler, handlerIndex: number) => (
                    <ListItem key={handlerIndex} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                      <Typography variant="body1" fontWeight="bold">
                        {handler.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {handler.description}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        {handler.input_variables.map((variable: string, varIndex: number) => (
                          <Chip
                            key={varIndex}
                            label={variable}
                            size="small"
                            sx={{ mr: 1, mb: 1 }}
                          />
                        ))}
                      </Box>
                    </ListItem>
                  ))}
                </List>
              </ListItem>
            ))}
          </List>

          <Typography variant="subtitle2" sx={{ mt: 2 }}>
            Output Variable: {config.output_variable}
          </Typography>
        </AccordionDetails>
      </Accordion>
    );
  };

  const renderParallelization = (): React.ReactElement | null => {
    if (!isParallelizationConfig(config)) return null;
    return (
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">⚡ Parallelization Workflow</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="subtitle1" gutterBottom>
            Description: {config.description}
          </Typography>
          
          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Input Variables:
          </Typography>
          <Box sx={{ mb: 2 }}>
            {config.input_variables.map((variable: string, index: number) => (
              <Chip
                key={index}
                label={variable}
                size="small"
                sx={{ mr: 1, mb: 1 }}
              />
            ))}
          </Box>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Steps:
          </Typography>
          <List>
            {config.steps.map((step: ParallelizationStep, index: number) => (
              <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {index + 1}. {step.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {step.description}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Chip
                    label={`Mode: ${step.execution_mode}`}
                    color="primary"
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  <Chip
                    label={`Workers: ${step.max_workers}`}
                    color="primary"
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  <Chip
                    label={`Aggregation: ${step.aggregation_strategy.type}`}
                    color="primary"
                    size="small"
                  />
                </Box>
                
                <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                  Parallel Tasks:
                </Typography>
                <List sx={{ pl: 2 }}>
                  {step.tasks.map((task: ParallelTask, taskIndex: number) => (
                    <ListItem key={taskIndex} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                      <Typography variant="body1" fontWeight="bold">
                        {task.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {task.description}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        {task.input_variables.map((variable: string, varIndex: number) => (
                          <Chip
                            key={varIndex}
                            label={variable}
                            size="small"
                            sx={{ mr: 1, mb: 1 }}
                          />
                        ))}
                      </Box>
                    </ListItem>
                  ))}
                </List>
              </ListItem>
            ))}
          </List>

          <Typography variant="subtitle2" sx={{ mt: 2 }}>
            Output Variable: {config.output_variable}
          </Typography>
        </AccordionDetails>
      </Accordion>
    );
  };

  const renderOrchestrator = (): React.ReactElement | null => {
    if (!isOrchestratorConfig(config)) return null;
    return (
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">🎭 Orchestrator Workflow</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="subtitle1" gutterBottom>
            Description: {config.description}
          </Typography>
          
          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Input Variables:
          </Typography>
          <Box sx={{ mb: 2 }}>
            {config.input_variables.map((variable: string, index: number) => (
              <Chip
                key={index}
                label={variable}
                size="small"
                sx={{ mr: 1, mb: 1 }}
              />
            ))}
          </Box>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Tasks:
          </Typography>
          <List>
            {config.tasks.map((task, index: number) => (
              <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {index + 1}. {task.type}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {task.description}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  {task.input_variables.map((variable: string, varIndex: number) => (
                    <Chip
                      key={varIndex}
                      label={variable}
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))}
                </Box>
              </ListItem>
            ))}
          </List>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Orchestrator Configuration:
          </Typography>
          <Box sx={{ mb: 2 }}>
            <Chip
              label={`Max Workers: ${config.orchestrator_config.max_workers}`}
              color="primary"
              size="small"
              sx={{ mr: 1, mb: 1 }}
            />
            <Chip
              label={`Retry Attempts: ${config.orchestrator_config.retry_attempts}`}
              color="primary"
              size="small"
              sx={{ mr: 1, mb: 1 }}
            />
          </Box>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Worker Configurations:
          </Typography>
          <List>
            {config.worker_configs.map((worker, index: number) => (
              <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                <Typography variant="body1" fontWeight="bold">
                  {worker.type}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {worker.description}
                </Typography>
              </ListItem>
            ))}
          </List>

          <Typography variant="subtitle2" sx={{ mt: 2 }}>
            Output Variable: {config.output_variable}
          </Typography>
        </AccordionDetails>
      </Accordion>
    );
  };

  const renderEvaluatorOptimizer = (): React.ReactElement | null => {
    if (!isEvaluatorOptimizerConfig(config)) return null;
    return (
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">🔄 Evaluator-Optimizer Workflow</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="subtitle1" gutterBottom>
            Description: {config.description}
          </Typography>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Task Description:
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {config.task_description}
          </Typography>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Input Variables:
          </Typography>
          <Box sx={{ mb: 2 }}>
            {config.input_variables.map((variable: string, index: number) => (
              <Chip
                key={index}
                label={variable}
                size="small"
                sx={{ mr: 1, mb: 1 }}
              />
            ))}
          </Box>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Evaluation Criteria:
          </Typography>
          <List>
            {config.evaluation_criteria.map((criterion: EvaluationCriterion, index: number) => (
              <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                <Typography variant="body1" fontWeight="bold">
                  {criterion.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {criterion.description}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Chip
                    label={`Weight: ${criterion.weight}`}
                    color="primary"
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  <Chip
                    label={criterion.required ? 'Required' : 'Optional'}
                    color={criterion.required ? 'error' : 'default'}
                    size="small"
                  />
                </Box>
              </ListItem>
            ))}
          </List>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Configuration:
          </Typography>
          <Box sx={{ mb: 2 }}>
            <Chip
              label={`Max Iterations: ${config.max_iterations}`}
              color="primary"
              size="small"
              sx={{ mr: 1, mb: 1 }}
            />
            <Chip
              label={`Success Threshold: ${(config.success_threshold * 100).toFixed(0)}%`}
              color="primary"
              size="small"
              sx={{ mr: 1, mb: 1 }}
            />
          </Box>

          <Typography variant="subtitle2" sx={{ mt: 2 }}>
            Output Variable: {config.output_variable}
          </Typography>
        </AccordionDetails>
      </Accordion>
    );
  };

  return (
    <Box sx={{ mt: 3, mb: 3 }}>
      <Typography variant="h5" gutterBottom>
        Configuration Overview
      </Typography>
      
      {renderPromptChain()}
      {renderRouting()}
      {renderParallelization()}
      {renderOrchestrator()}
      {renderEvaluatorOptimizer()}
      {renderAgents()}
      {renderTools()}
      {renderNodes()}
      {renderEdges()}
      {renderWorkflow()}
    </Box>
  );
};

export default ConfigViewer;
