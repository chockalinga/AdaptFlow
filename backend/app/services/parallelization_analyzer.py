from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import json
from langchain_aws import BedrockLLM
import boto3
import re
import os

class OutputFormat(BaseModel):
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            "type": self.type,
            "properties": self.properties
        }

    def json(self, *args, **kwargs) -> str:
        return json.dumps(self.dict())

    @classmethod
    def create_default(cls) -> 'OutputFormat':
        return cls(
            type="object",
            properties={
                "result": {
                    "type": "string",
                    "description": "The result of the task"
                }
            }
        )

    class Config:
        frozen = True

class ParallelTask(BaseModel):
    name: str
    description: str = Field(default="Execute parallel task")
    prompt_template: str
    input_variables: List[str] = Field(default_factory=list)
    output_format: OutputFormat = Field(
        default_factory=OutputFormat.create_default
    )

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "prompt_template": self.prompt_template,
            "input_variables": self.input_variables,
            "output_format": self.output_format.dict()
        }

    def json(self, *args, **kwargs) -> str:
        return json.dumps(self.dict())

    class Config:
        frozen = True

class AggregationStrategy(BaseModel):
    type: str = Field(default="merge")  # 'merge', 'vote', or 'consensus'
    threshold: Optional[float] = Field(default=0.8)
    combine_method: Optional[str] = Field(default=None)

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            "type": self.type,
            "threshold": self.threshold,
            "combine_method": self.combine_method
        }

    def json(self, *args, **kwargs) -> str:
        return json.dumps(self.dict())

    class Config:
        frozen = True

class ParallelizationStep(BaseModel):
    name: str
    description: str = Field(default="Execute parallel step")
    execution_mode: str = Field(default="sectioning")  # 'sectioning' or 'voting'
    tasks: List[ParallelTask]
    max_workers: int = Field(default=3)
    aggregation_strategy: AggregationStrategy = Field(
        default_factory=lambda: AggregationStrategy(type="merge", threshold=0.8)
    )
    output_key: str = Field(default="result")
    input_variables: List[str] = Field(default_factory=list)
    output_format: OutputFormat = Field(
        default_factory=lambda: OutputFormat(type="object", properties={})
    )

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "execution_mode": self.execution_mode,
            "tasks": [task.dict() for task in self.tasks],
            "max_workers": self.max_workers,
            "aggregation_strategy": self.aggregation_strategy.dict(),
            "output_key": self.output_key,
            "input_variables": self.input_variables,
            "output_format": self.output_format.dict()
        }

    def json(self, *args, **kwargs) -> str:
        return json.dumps(self.dict())

    class Config:
        frozen = True

class ParallelizationAnalysis(BaseModel):
    steps: List[ParallelizationStep]
    input_variables: List[str]
    output_variable: str

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            "steps": [step.dict() for step in self.steps],
            "input_variables": self.input_variables,
            "output_variable": self.output_variable
        }

    def json(self, *args, **kwargs) -> str:
        return json.dumps(self.dict())

    class Config:
        frozen = True

class ParallelizationAnalyzer:
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

    def analyze_requirements(self, description: str) -> ParallelizationAnalysis:
        """Analyze requirements and determine optimal parallelization configuration"""
        self._initialize_model()

        # Step 1: Analyze core parallelization requirements
        core_analysis_prompt = f"""You are an expert at designing parallelization workflows for LLMs. First, analyze the core requirements:

        Requirement: {description}

        Determine:
        1. Main parallelization objective
        2. Required input data
        3. Expected final output
        4. Parallel tasks to execute
        5. Execution mode (sectioning or voting)
        6. Aggregation strategy

        Return a JSON object with this structure:
        {{
            "objective": "clear statement of the parallelization goal",
            "inputs": ["list", "of", "required", "inputs"],
            "output": "expected final output format",
            "tasks": ["task1", "task2", "etc"],
            "execution_mode": "sectioning or voting",
            "aggregation_strategy": {{
                "type": "merge/vote/consensus",
                "threshold": 0.8,  # for voting/consensus
                "combine_method": "method to combine results"
            }}
        }}

        Return only the JSON object, no other text.
        """

        core_response = self.model.invoke(core_analysis_prompt)
        core_analysis = json.loads(self._extract_json(core_response))

        # Step 2: Design parallelization details
        parallel_prompt = f"""Based on the core analysis, design detailed parallelization configuration.

        Core Analysis: {json.dumps(core_analysis, indent=2)}

        For the parallelization workflow, determine:
        1. Task definitions and prompts
        2. Input/output formats for each task
        3. Execution settings
        4. Result aggregation details

        Return a JSON object with this structure:
        {{
            "steps": [
                {{
                    "name": "step_name",
                    "description": "step description",
                    "execution_mode": "{core_analysis['execution_mode']}",
                    "tasks": [
                        {{
                            "name": "task_name",
                            "description": "task purpose",
                            "prompt_template": "prompt for this task",
                            "input_variables": ["required", "inputs"],
                            "output_format": {{
                                "type": "object",
                                "properties": {{}}
                            }}
                        }}
                    ],
                    "max_workers": 3,
                    "aggregation_strategy": {json.dumps(core_analysis['aggregation_strategy'])},
                    "output_key": "result",
                    "input_variables": ["required", "inputs"],
                    "output_format": {{
                        "type": "object",
                        "properties": {{}}
                    }}
                }}
            ]
        }}

        Ensure:
        1. Clear task definitions
        2. Proper input/output formats
        3. Appropriate execution settings
        4. Consistent variable naming

        Return only the JSON object, no other text.
        """

        parallel_response = self.model.invoke(parallel_prompt)
        parallel_analysis = json.loads(self._extract_json(parallel_response))

        # Step 3: Validate and combine results
        try:
            required_core_fields = {"objective", "inputs", "output", "tasks"}
            if not all(field in core_analysis for field in required_core_fields):
                raise ValueError(f"Missing required core fields. Found: {set(core_analysis.keys())}")

            if "steps" not in parallel_analysis:
                raise ValueError("Parallelization analysis missing 'steps' field")

            for step in parallel_analysis["steps"]:
                step["name"] = self._normalize_identifier(step["name"])

                for task in step["tasks"]:
                    task["name"] = self._normalize_identifier(task["name"])
                    task["prompt_template"] = task["prompt_template"].replace("{", "{{").replace("}", "}}")

                required_step_fields = {
                    "name", "description", "execution_mode", "tasks",
                    "max_workers", "aggregation_strategy", "output_key",
                    "input_variables", "output_format"
                }
                if not all(field in step for field in required_step_fields):
                    raise ValueError(f"Step {step.get('name', 'unknown')} missing required fields")

            # Convert raw dictionaries to proper model instances
            steps = []
            for step in parallel_analysis["steps"]:
                # Convert output format
                step["output_format"] = OutputFormat(**step["output_format"])
                
                # Convert tasks
                tasks = []
                for task in step["tasks"]:
                    task["output_format"] = OutputFormat(**task["output_format"])
                    tasks.append(ParallelTask(**task))
                step["tasks"] = tasks
                
                # Convert aggregation strategy
                step["aggregation_strategy"] = AggregationStrategy(**step["aggregation_strategy"])
                
                # Create step
                steps.append(ParallelizationStep(**step))

            return ParallelizationAnalysis(
                steps=steps,
                input_variables=core_analysis["inputs"],
                output_variable=core_analysis["output"]
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse parallelization analysis: {str(e)}")

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling various formats"""
        # Try to find JSON between triple backticks
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
