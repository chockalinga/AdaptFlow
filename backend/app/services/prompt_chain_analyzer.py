from typing import Dict, List, Any, Optional, Type, Callable, Union
from pydantic import BaseModel, Field, ValidationError, parse_obj_as
import json
from langchain_aws import BedrockLLM
import boto3
import re
import os

def normalize_context(context: Dict[str, Any], step_inputs: List[str]) -> Dict[str, Any]:
    """Normalize context keys to match step input requirements."""
    normalized = {}
    for input_var in step_inputs:
        snake_case = input_var.lower().replace(" ", "_")
        if input_var in context:
            normalized[snake_case] = context[input_var]
        elif snake_case in context:
            normalized[snake_case] = context[snake_case]
    return normalized

class OutputFormat(BaseModel):
    type: str = "json"
    schema: Dict[str, Any] = Field(default_factory=dict)

    def is_array_type(self) -> bool:
        """Check if this output format expects an array."""
        return self.type == "array" or (
            self.schema.get("type") == "array" if self.schema else False
        )

class StepOutput(BaseModel):
    data: Union[Dict[str, Any], List[Any]]

    def validate_output(self) -> bool:
        return isinstance(self.data, (dict, list))

    @classmethod
    def parse_response(cls, response: str, output_format: OutputFormat) -> 'StepOutput':
        data = json.loads(response)
        # Keep array structure if specified in schema
        if output_format.is_array_type() and not isinstance(data, list):
            data = [data] if data else []
        elif not isinstance(data, dict):
            data = {"result": data} if data else {"result": None}
        return cls(data=data)

    class Config:
        extra = "forbid"

class PromptChainStep(BaseModel):
    name: str
    description: str
    prompt_template: str
    output_key: str
    input_variables: List[str]
    output_format: OutputFormat = Field(default_factory=OutputFormat)
    has_gate: bool = False
    gate_condition: Optional[str] = None

    def normalize_inputs(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize input variables for this step."""
        return normalize_context(context, self.input_variables)

class PromptChainAnalysis(BaseModel):
    steps: List[PromptChainStep]
    input_variables: List[str]
    output_variable: str

class PromptChainAnalyzer:
    def __init__(self):
        self.model_id = os.getenv("BEDROCK_MODEL") or "anthropic.claude-v2"
        self.parameters = {
            "temperature": 0,
            "max_tokens_to_sample": 4000
        }
        self.model = None

    def _initialize_model(self) -> None:
        if self.model is None:
            aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            aws_region = os.getenv("AWS_REGION")
            if not (aws_access_key and aws_secret_key and aws_region):
                raise ValueError(
                    "AWS credentials missing. Please ensure AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION are set."
                )
            bedrock = boto3.client(
                "bedrock-runtime",
                region_name=aws_region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
            )
            self.model = BedrockLLM(
                client=bedrock,
                model_id=self.model_id,
                model_kwargs=self.parameters,
            )

    def _normalize_identifier(self, name: str) -> str:
        name = name.lower().strip()
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        return re.sub(r'_+', '_', name)
    
    def analyze_requirements(self, description: str) -> PromptChainAnalysis:
        """Analyze requirements and determine optimal prompt chain steps"""
        self._initialize_model()

        # Step 1: Analyze core requirements
        core_analysis_prompt = f"""You are an expert at designing prompt chains. First, analyze the core requirements:

        Requirement: {description}

        Determine:
        1. Main objective
        2. Required input data
        3. Expected final output
        4. Key processing steps needed
        5. Data dependencies between steps
        6. Validation requirements

        Return a JSON object with this structure:
        {{
            "objective": "clear statement of the main goal",
            "inputs": ["list", "of", "required", "inputs"],
            "output": "expected final output format",
            "processing_steps": ["step1", "step2", "etc"],
            "dependencies": {{"step2": ["step1"], "step3": ["step1", "step2"]}},
            "validation_needs": ["list", "of", "validation", "requirements"]
        }}

        Return only the JSON object, no other text.
        """

        core_response = self.model.invoke(core_analysis_prompt)
        core_analysis = json.loads(self._extract_json(core_response))

        # Step 2: Design step details
        schema_examples = '''
{
  "financial_metrics": {
    "type": "object",
    "properties": {
      "revenue": { "type": "number" },
      "profit": { "type": "number" },
      "growth": { "type": "number" }
    },
    "required": ["revenue", "profit"]
  },
  "company_data": {
    "type": "object",
    "properties": {
      "name": { "type": "string" },
      "industry": { "type": "string" },
      "metrics": {
        "type": "object",
        "properties": {
          "employees": { "type": "number" },
          "locations": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  },
  "analysis_results": {
    "type": "object",
    "properties": {
      "score": { "type": "number" },
      "categories": { "type": "array", "items": { "type": "string" } },
      "details": {
        "type": "object",
        "properties": {
          "strengths": { "type": "array", "items": { "type": "string" } },
          "weaknesses": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
'''

        steps_prompt = f"""Based on the core analysis, design detailed steps for the prompt chain.

        Core Analysis: {json.dumps(core_analysis, indent=2)}

        For each processing step, determine:
        1. Precise input requirements
        2. Specific LLM prompt template
        3. Expected output format with schema following JSON Schema format:
           - Every field must have a "type" property
           - Valid types are: "string", "number", "array", "object", "boolean"
           - Schema Examples (follow these patterns):
{schema_examples}
           - Key points:
             1. Use "type" for every field
             2. Use "properties" for object fields
             3. Use "items" for array fields
             4. Use "required" for mandatory fields
             5. Keep schemas focused and well-structured
             6. Use nested objects for complex data
             7. Use arrays for lists of items
        4. Validation criteria and gates

        Return a JSON object with this structure:
        {{
            "steps": [
                {{
                    "name": "step_name",
                    "description": "detailed description of purpose",
                    "prompt_template": "LLM prompt with {{variables}}",
                    "output_key": "variable_name",
                    "input_variables": ["required", "inputs"],
                    "output_format": {{
                        "type": "json",
                        "schema": {{}}  # Schema will be determined based on step requirements
                    }},
                    "has_gate": True/False,
                    "gate_condition": "specific validation criteria"
                }}
            ]
        }}

        Ensure:
        1. Each step has a clear, focused purpose
        2. Validation gates for critical steps
        3. Descriptive variable names
        4. Clear input/output formats
        5. Proper data flow matching dependencies

        Return only the JSON object, no other text.
        """

        steps_response = self.model.invoke(steps_prompt)
        steps_analysis = json.loads(self._extract_json(steps_response))

        # Step 3: Validate and combine results
        try:
            required_core_fields = {"objective", "inputs", "output", "processing_steps"}
            if not all(field in core_analysis for field in required_core_fields):
                raise ValueError(f"Missing required core fields. Found: {set(core_analysis.keys())}")

            if "steps" not in steps_analysis:
                raise ValueError("Steps analysis missing 'steps' field")

            for step in steps_analysis["steps"]:
                step["name"] = self._normalize_identifier(step["name"])
                step["prompt_template"] = step["prompt_template"].replace("{", "{{").replace("}", "}}")

                if not step.get("output_format"):
                    step["output_format"] = {"type": "json", "schema": {}}

                if not step["output_format"].get("schema"):
                    step["output_format"]["schema"] = {
                        "type": "object",
                        "properties": {
                            "result": {"type": "string"}
                        },
                        "required": ["result"]
                    }

                required_step_fields = {
                    "name", "description", "prompt_template", "output_key",
                    "input_variables", "output_format"
                }
                if not all(field in step for field in required_step_fields):
                    raise ValueError(f"Step {step.get('name', 'unknown')} missing required fields")

                if not isinstance(step["name"], str):
                    raise ValueError("Step name must be a string")
                if not isinstance(step["description"], str):
                    raise ValueError("Step description must be a string")
                if not isinstance(step["prompt_template"], str):
                    raise ValueError("Step prompt_template must be a string")
                if not isinstance(step["output_key"], str):
                    raise ValueError("Step output_key must be a string")
                if not isinstance(step["input_variables"], list):
                    raise ValueError("Step input_variables must be a list")
                for var in step["input_variables"]:
                    if not isinstance(var, str):
                        raise ValueError(f"Input variable must be a string: {var}")

            return PromptChainAnalysis(
                steps=[PromptChainStep(**step) for step in steps_analysis["steps"]],
                input_variables=core_analysis["inputs"],
                output_variable=core_analysis["output"]
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse workflow analysis: {str(e)}")

    def _generate_initial_code(self, analysis: PromptChainAnalysis) -> str:
        """Generate initial implementation code based on the prompt chain analysis."""
        self._initialize_model()

        code_parts = []  # Store code parts in a list

        # Imports and setup
        code_parts.append("""from typing import Dict, List, Any, Optional, Callable, Type
from pydantic import BaseModel, Field, ValidationError, create_model
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
class ChainState(BaseModel):
    context: Dict[str, Any]
    current_step: str
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    class Config:
        extra = "forbid"
""")

        # Step registry
        code_parts.append("""
step_functions: Dict[str, Callable] = {}

def register_step(name: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        step_functions[name] = func
        return func
    return decorator
""")

        # Validation helpers
        code_parts.append("""
def validate_json(data: Any) -> bool:
    try:
        return isinstance(data, dict)
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False

def parse_llm_response(response: str, model: Type[BaseModel]) -> BaseModel:
    try:
        data = json.loads(response)
        return model.parse_obj(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {e}")
    except ValidationError as e:
        raise ValueError(f"Response validation failed: {e}")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
async def safe_ainvoke(llm, messages):
    return await llm.ainvoke(messages)
""")

        # Base output model
        code_parts.append("""
class StepOutput(BaseModel):
    data: Dict[str, Any]

    def validate_output(self) -> bool:
        return validate_json(self.data)

    class Config:
        extra = "forbid"
""")

        # Step models
        for step in analysis.steps:
            model_name = f"{step.name.title().replace('_', '')}Output"
            code_parts.append(f"""
class {model_name}(StepOutput):
    \"\"\"Output model for {step.description}\"\"\"
    pass
""")

        # Prompt templates
        for step in analysis.steps:
            prompt_string = step.prompt_template.replace('"""', '\"\"\"')
            code_parts.append(f"""
{step.name}_prompt = ChatPromptTemplate.from_messages([
    ("system", \"\"\"Execute {step.description}.
Output must be valid JSON matching this schema:
{json.dumps(step.output_format.schema, indent=2)}
\"\"\"),
    ("human", f"{prompt_string}")
])
""")

        # Step implementations
        for step in analysis.steps:
            output_model = f"{step.name.title().replace('_', '')}Output"
            code_parts.append(f"""
@register_step("{step.name}")
async def {step.name}(state: ChainState, {', '.join(f'{var}: str' for var in step.input_variables)}) -> {output_model}:
    try:
        logger.info(f"Executing {step.name}")
        messages = {step.name}_prompt.format_messages(
            {', '.join(f'{var}={var}' for var in step.input_variables)}
        )
        llm = ChatOpenAI(temperature=0.7)
        response = await safe_ainvoke(llm, messages)

        try:
            data = json.loads(response.content)
            if not isinstance(data, dict):
                data = {{"result": data}}
        except json.JSONDecodeError:
            data = {{"result": response.content}}

        result = {output_model}(data=data)

        if {str(step.has_gate).capitalize()}:
            logger.info(f"Checking gate condition for {step.name}")
            if not result.validate_output():
                raise ValueError(f"Gate condition failed for {step.name}")

        logger.info(f"Successfully completed {step.name}")
        return result

    except Exception as e:
        logger.error(f"Error in {step.name}: {{str(e)}}")
        raise
""")

        # Chain executor
        code_parts.append(f"""
class PromptChainExecutor:
    def __init__(self, steps):
        self.logger = logging.getLogger(__name__)
        self.steps = steps

    async def execute_chain(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            state = ChainState(context=initial_context, current_step="", outputs={{}})
            for step in self.steps:
                state.current_step = step["name"]
                self.logger.info(f"Executing step: {{step['name']}}")
                inputs = {{var: state.context[var] for var in step["input_variables"] if var in state.context}}
                if step["name"] not in step_functions:
                    raise ValueError(f"Step function {{step['name']}} not found")
                result = await step_functions[step["name"]](state, **inputs)
                state.outputs[step["output_key"]] = result.dict()
                state.context.update(result.dict())
                self.logger.info(f"Completed step: {{step['name']}}")

            self.logger.info("Chain execution completed")
            return state.outputs
        except Exception as e:
            self.logger.error(f"Chain execution failed: {{str(e)}}")
            raise
""")

        # Main block
        code_parts.append(f"""
if __name__ == "__main__":
    async def main():
        steps = {json.dumps([step.dict() for step in analysis.steps], indent=4)}
        executor = PromptChainExecutor(steps)
        context = {{
            # Provide required input variables here, e.g.
            {', '.join(f'"{var}": "sample_value"' for var in analysis.input_variables)}
        }}
        result = await executor.execute_chain(context)
        print(json.dumps(result, indent=2))

    asyncio.run(main())
""")

        # Join all code parts
        return "".join(code_parts)

    def validate_and_improve_code(self, code: str, analysis: PromptChainAnalysis) -> str:
        """Validate and improve the generated code for better sequential prompt chaining."""
        self._initialize_model()
        
        validation_prompt = f"""You are an expert Python developer specializing in LangChain and prompt chaining.
        
        The code implements a prompt chain with these steps:
        {json.dumps([{
            "name": step.name,
            "description": step.description,
            "input_variables": step.input_variables,
            "output_key": step.output_key,
            "has_gate": step.has_gate,
            "gate_condition": step.gate_condition,
            "output_format": {
                "type": step.output_format.type,
                "schema": step.output_format.schema
            }
        } for step in analysis.steps], indent=2)}
        
        Input Variables: {analysis.input_variables}
        Output Variable: {analysis.output_variable}

        CRITICAL LANGCHAIN RULES:
        1. LLM Usage:
           - OpenAI LLM is synchronous - do NOT use await with .generate() or .predict()
           - Use ChatOpenAI().predict() for sync calls
           - Use ChatOpenAI().apredict() for async calls
           - Do NOT mix sync/async calls
        
        2. Chain Construction:
           - LLMChain only accepts: llm, prompt, output_key
           - Do NOT pass input_key, output_format, or custom args
           - Use LLMChain.predict() for sync execution
           - Use LLMChain.apredict() for async execution
        
        3. Imports & Classes:
           - Use correct imports from langchain.chains, langchain.prompts
           - Do NOT import non-existent classes (e.g., Schema)
           - Do NOT mix LangGraph concepts with core LangChain
           - Use proper LangChain base classes
        
        4. Chain Execution:
           - Do NOT add .run() to classes that don't have it
           - Use proper chain execution methods (predict/apredict)
           - Handle inputs/outputs according to chain type
           - Follow chain-specific execution patterns
        
        5. Custom Implementation:
           - Use custom classes for complex logic
           - Implement proper async patterns
           - Handle state management yourself
           - Use proper error handling
        
        Review and improve this code for:
        
        1. Proper Async Implementation:
           - Use proper async/await patterns
           - Handle async LLM calls correctly
           - Implement proper error handling
           - Add retry mechanisms
        
        2. State Management:
           - Implement custom state handling
           - Track step progress
           - Handle step dependencies
           - Validate step outputs
        
        3. Code Quality:
           - Clear type hints
           - Proper error messages
           - Comprehensive logging
           - Input validation
           - Output validation

        Return only the improved code between triple backticks, no other text.
        
        CODE TO REVIEW:
        ```python
        {code}
        ```
        """
        
        response = self.model.invoke(validation_prompt)
        return self._extract_code(response)

    def generate_code(self, analysis: PromptChainAnalysis) -> str:
        """Generate implementation code based on the prompt chain analysis."""
        # Generate initial code
        initial_code = self._generate_initial_code(analysis)
        
        # Validate and improve the code
        # improved_code = self.validate_and_improve_code(initial_code, analysis)
        
        return initial_code

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling various formats"""
        # Try to find JSON between triple backticks
        import re
        json_match = re.search(r'```(?:json)?\s*({\s*".*?})\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
            
        # Try to find JSON between single backticks
        json_match = re.search(r'`({\s*".*?})`', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
            
        # Try to find bare JSON object
        json_match = re.search(r'({\s*".*?})\s*$', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
            
        # If no JSON found, return the entire text (let JSON parser handle it)
        return text.strip()

    def _extract_code(self, text: str) -> str:
        """Extract code from text, handling various formats"""
        # Try to find code between triple backticks
        import re
        code_match = re.search(r'```(?:python)?\s*(.*?)\s*```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
            
        # If no code block found, return the entire text
        return text.strip()
