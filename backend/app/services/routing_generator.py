from typing import Dict, List, Any
import json
from .routing_analyzer import RoutingAnalyzer, RoutingAnalysis

class RoutingGenerator:
    def __init__(self):
        self.analyzer = RoutingAnalyzer()

    def generate(self, description: str) -> Dict[str, Any]:
        """
        Generate a routing workflow implementation based on the description.
        
        Args:
            description: User's requirement description
            
        Returns:
            Dict containing:
            - config: The analyzed workflow configuration
            - code: The generated implementation code
        """
        try:
            # Analyze requirements and generate routing configuration
            analysis = self.analyzer.analyze_requirements(description)
            
            # Generate implementation code
            code = self._generate_code(analysis)
            
            # Create configuration
            config = {
                "workflow_type": "routing",
                "description": description,
                "steps": [
                    {
                        "name": step.name,
                        "description": step.description,
                        "classifier_prompt": step.classifier_prompt,
                        "output_key": step.output_key,
                        "input_variables": step.input_variables,
                        "handlers": [handler.dict() for handler in step.handlers],
                        "output_format": step.output_format
                    }
                    for step in analysis.steps
                ],
                "input_variables": analysis.input_variables,
                "output_variable": analysis.output_variable
            }
            
            return {
                "config": config,
                "code": code
            }
            
        except Exception as e:
            raise ValueError(f"Failed to generate routing workflow: {str(e)}")

    def _generate_code(self, analysis: RoutingAnalysis) -> str:
        """Generate implementation code based on the routing analysis."""
        code_parts = []

        # Imports
        code_parts.append("""from typing import Dict, List, Any, Optional, Callable
from pydantic import BaseModel, Field, ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import logging
import json
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
""")

        # State management
        code_parts.append("""
class RoutingState(BaseModel):
    context: Dict[str, Any]
    current_step: str
    current_handler: str
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    class Config:
        extra = "forbid"
""")

        # Handler registry
        code_parts.append("""
handler_functions: Dict[str, Callable] = {}

def register_handler(name: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        handler_functions[name] = func
        return func
    return decorator
""")

        # Base output models
        code_parts.append("""
class HandlerOutput(BaseModel):
    data: Dict[str, Any]

    def validate_output(self) -> bool:
        return isinstance(self.data, dict)

    class Config:
        extra = "forbid"
""")

        # Generate handler models and implementations
        for step in analysis.steps:
            for handler in step.handlers:
                model_name = f"{handler.name.title().replace('_', '')}Output"
                code_parts.append(f"""
class {model_name}(HandlerOutput):
    \"\"\"Output model for {handler.description}\"\"\"
    pass

{handler.name}_prompt = ChatPromptTemplate.from_messages([
    ("system", \"\"\"Execute {handler.description}.
Output must be valid JSON matching this schema:
{json.dumps(handler.output_format, indent=2)}
\"\"\"),
    ("human", f"{handler.prompt_template}")
])

@register_handler("{handler.name}")
async def {handler.name}(state: RoutingState, {', '.join(f'{var}: str' for var in handler.input_variables)}) -> {model_name}:
    try:
        logger.info(f"Executing handler: {handler.name}")
        messages = {handler.name}_prompt.format_messages(
            {', '.join(f'{var}={var}' for var in handler.input_variables)}
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
        logger.info(f"Successfully completed handler: {handler.name}")
        return result

    except Exception as e:
        logger.error(f"Error in handler {handler.name}: {{str(e)}}")
        raise
""")

        # Generate classifier implementations
        for step in analysis.steps:
            code_parts.append(f"""
{step.name}_classifier_prompt = ChatPromptTemplate.from_messages([
    ("system", \"\"\"Analyze input and select appropriate handler.
Available handlers: {[h.name for h in step.handlers]}
Output must be valid JSON with format:
{{
    "selected_handler": "handler_name",
    "reasoning": "explanation for selection"
}}
\"\"\"),
    ("human", f"{step.classifier_prompt}")
])

async def {step.name}_classifier(state: RoutingState, {', '.join(f'{var}: str' for var in step.input_variables)}) -> str:
    try:
        logger.info(f"Executing classifier: {step.name}")
        messages = {step.name}_classifier_prompt.format_messages(
            {', '.join(f'{var}={var}' for var in step.input_variables)}
        )
        llm = ChatOpenAI(temperature=0.2)
        response = await llm.ainvoke(messages)

        try:
            result = json.loads(response.content)
            selected_handler = result["selected_handler"]
            logger.info(f"Selected handler: {{selected_handler}}")
            logger.info(f"Selection reasoning: {{result['reasoning']}}")
            return selected_handler
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Invalid classifier response: {{str(e)}}")

    except Exception as e:
        logger.error(f"Error in classifier {step.name}: {{str(e)}}")
        raise
""")

        # Routing executor
        code_parts.append(f"""
class RoutingExecutor:
    def __init__(self, steps):
        self.logger = logging.getLogger(__name__)
        self.steps = steps

    async def execute_routing(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            state = RoutingState(
                context=initial_context,
                current_step="",
                current_handler=""
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

                # Run classifier to select handler
                classifier_func = globals()[f"{{step['name']}}_classifier"]
                selected_handler = await classifier_func(state, **inputs)
                state.current_handler = selected_handler

                # Execute selected handler
                if selected_handler not in handler_functions:
                    raise ValueError(f"Handler {{selected_handler}} not found")

                handler_func = handler_functions[selected_handler]
                result = await handler_func(state, **inputs)
                
                # Store results
                state.outputs[step["output_key"]] = result.dict()
                state.context.update(result.dict())

                self.logger.info(f"Completed step: {{step['name']}}")

            self.logger.info("Routing execution completed")
            return state.outputs

        except Exception as e:
            self.logger.error(f"Routing execution failed: {{str(e)}}")
            raise
""")

        # Main block
        code_parts.append(f"""
if __name__ == "__main__":
    async def main():
        steps = {json.dumps([{
            "name": step.name,
            "description": step.description,
            "input_variables": step.input_variables,
            "output_key": step.output_key
        } for step in analysis.steps], indent=4)}
        
        executor = RoutingExecutor(steps)
        context = {{
            # Provide required input variables here, e.g.
            {', '.join(f'"{var}": "sample_value"' for var in analysis.input_variables)}
        }}
        result = await executor.execute_routing(context)
        print(json.dumps(result, indent=2))

    asyncio.run(main())
""")

        return "\n".join(code_parts)
