from typing import Dict, List, Any
import json
import os
from .parallelization_analyzer import ParallelizationAnalyzer, ParallelizationAnalysis

class ParallelizationGenerator:
    def __init__(self):
        self.analyzer = ParallelizationAnalyzer()

    def generate(self, description: str) -> Dict[str, Any]:
        """
        Generate a parallelization workflow implementation based on the description.
        
        Args:
            description: User's requirement description
            
        Returns:
            Dict containing:
            - config: The analyzed workflow configuration
            - code: The generated implementation code
        """
        try:
            # Analyze requirements and generate parallelization configuration
            analysis = self.analyzer.analyze_requirements(description)
            
            # Generate implementation code
            code = self._generate_code(analysis)
            
            # Create configuration using model's dict method for proper serialization
            analysis_dict = analysis.dict()
            config = {
                "workflow_type": "parallelization",
                "description": description,
                "steps": analysis_dict["steps"],
                "input_variables": analysis_dict["input_variables"],
                "output_variable": analysis_dict["output_variable"]
            }
            
            return {
                "config": config,
                "code": code
            }
            
        except Exception as e:
            raise ValueError(f"Failed to generate parallelization workflow: {str(e)}")

    def _generate_code(self, analysis: ParallelizationAnalysis) -> str:
        """Generate implementation code based on the parallelization analysis."""
        code_parts = []

        # Imports
        imports = '''from typing import Dict, List, Any, Optional, Callable
from pydantic import BaseModel, Field, ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import logging
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
'''
        code_parts.append(imports)

        # State management
        state_model = '''
class ParallelState(BaseModel):
    context: Dict[str, Any]
    current_step: str
    current_task: str
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    class Config:
        extra = "forbid"
'''
        code_parts.append(state_model)

        # Task registry
        registry = '''
task_functions: Dict[str, Callable] = {}

def register_task(name: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        task_functions[name] = func
        return func
    return decorator
'''
        code_parts.append(registry)

        # Base output models
        base_models = '''
class TaskOutput(BaseModel):
    data: Dict[str, Any]

    def validate_output(self) -> bool:
        return isinstance(self.data, dict)

    class Config:
        extra = "forbid"
'''
        code_parts.append(base_models)

        # Generate task models and implementations
        for step in analysis.steps:
            for task in step.tasks:
                # Create unique task name by combining step and task names
                unique_task_name = f"{step.name}_{task.name}"
                model_name = f"{unique_task_name.title().replace('_', '')}Output"
                task_code = f'''
class {model_name}(TaskOutput):
    """Output model for {task.description}"""
    pass

{unique_task_name}_prompt = ChatPromptTemplate.from_messages([
    ("system", """Execute {task.description}.
Output must be valid JSON matching this schema:
{json.dumps(task.output_format.dict(), indent=2)}
"""),
    ("human", f"{task.prompt_template}")
])

@register_task(name="{unique_task_name}")
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10),
    retry=retry_if_exception_type((json.JSONDecodeError, ValidationError))
)
async def {unique_task_name}(state: ParallelState, {', '.join(f'{var}: str' for var in task.input_variables)}) -> {model_name}:
    try:
        logger.info(f"Executing task: {unique_task_name}")
        messages = {unique_task_name}_prompt.format_messages(
            {', '.join(f'{var}={var}' for var in task.input_variables)}
        )
        llm = ChatOpenAI(temperature=0.7)
        response = await llm.ainvoke(messages)

        try:
            data = json.loads(response.content)
            if not isinstance(data, dict):
                data = {{"result": data}}
        except json.JSONDecodeError:
            data = {{"result": response.content}}

        result = {model_name}(data=data)
        logger.info(f"Successfully completed task: {unique_task_name}")
        return result

    except Exception as e:
        logger.error(f"Error in task {task.name}: {{str(e)}}")
        raise
'''
                code_parts.append(task_code)

        # Result aggregation functions
        aggregation = '''
def merge_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    merged = {}
    for result in results:
        merged.update(result)
    return merged

def vote_results(results: List[Dict[str, Any]], threshold: float = 0.8) -> Dict[str, Any]:
    votes = {}
    # Convert each result to a string for hashing
    result_strings = [json.dumps(result, sort_keys=True) for result in results]
    
    # Count votes for each unique result
    for result_str in result_strings:
        votes[result_str] = votes.get(result_str, 0) + 1

    total_votes = len(results)
    consensus = {}
    
    # Add results that meet the threshold to consensus
    for result_str, vote_count in votes.items():
        if vote_count / total_votes >= threshold:
            consensus.update(json.loads(result_str))
    
    return consensus

def aggregate_results(results: List[Dict[str, Any]], strategy: Dict[str, Any]) -> Dict[str, Any]:
    if strategy["type"] == "merge":
        return merge_results(results)
    elif strategy["type"] in ["vote", "consensus"]:
        return vote_results(results, strategy.get("threshold", 0.8))
    else:
        raise ValueError(f"Unknown aggregation strategy: {strategy['type']}")
'''
        code_parts.append(aggregation)

        # Parallelization executor
        executor = f'''
class ParallelizationExecutor:
    def __init__(self, steps):
        self.logger = logging.getLogger(__name__)
        self.steps = steps

    async def execute_parallel(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            state = ParallelState(
                context=initial_context,
                current_step="",
                current_task=""
            )

            for step in self.steps:
                state.current_step = step["name"]
                self.logger.info(f"Processing step: {{step['name']}}")

                # Get inputs for this step
                inputs = {{
                    var: state.context[var]
                    for var in step["input_variables"]
                    if var in state.context
                }}

                # Execute tasks in parallel
                tasks = []
                for task in step["tasks"]:
                    # Create unique task name by combining step and task names
                    unique_task_name = f"{{step['name']}}_{{task['name']}}"
                    task_func = task_functions[unique_task_name]
                    tasks.append(task_func(state, **inputs))

                # Wait for all tasks to complete
                results = await asyncio.gather(*tasks)
                results = [r.data for r in results]

                # Aggregate results
                aggregated_result = aggregate_results(
                    results,
                    step["aggregation_strategy"]
                )
                
                # Store results
                state.outputs[step["output_key"]] = aggregated_result
                state.context.update(aggregated_result)

                self.logger.info(f"Completed step: {{step['name']}}")

            self.logger.info("Parallelization execution completed")
            return state.outputs

        except Exception as e:
            self.logger.error(f"Parallelization execution failed: {{str(e)}}")
            raise
'''
        code_parts.append(executor)

        # Main block with normalized input keys
        main_block = f'''
if __name__ == "__main__":
    async def main():
        steps = {json.dumps([step.dict() for step in analysis.steps], indent=4)}
        
        executor = ParallelizationExecutor(steps)
        context = {{
            # Input variables in snake_case format
            {', '.join(f'"{var.lower().replace(" ", "_")}": "sample_value"' for var in analysis.input_variables)}
        }}
        result = await executor.execute_parallel(context)
        print(json.dumps(result, indent=2))

    asyncio.run(main())
'''
        code_parts.append(main_block)

        return "\n".join(code_parts)
