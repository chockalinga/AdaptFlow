from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import json
from langchain_aws import BedrockLLM
import boto3
import re
import os

class EvaluationCriteria(BaseModel):
    """Model for evaluation criteria configuration."""
    name: str
    description: str
    weight: float = Field(default=1.0)
    required: bool = Field(default=True)

class EvaluatorOptimizerConfig(BaseModel):
    """Configuration for the evaluator-optimizer workflow."""
    generator_prompt: str
    evaluator_prompt: str
    max_iterations: int = Field(default=5)
    success_threshold: float = Field(default=0.8)
    evaluation_criteria: List[EvaluationCriteria]
    output_format: Dict[str, Any] = Field(default_factory=dict)

class EvaluatorOptimizerAnalysis(BaseModel):
    """Analysis results for evaluator-optimizer workflow."""
    config: EvaluatorOptimizerConfig
    input_variables: List[str]
    output_variable: str
    task_description: str
    evaluation_format: Dict[str, Any]

class EvaluatorOptimizerAnalyzer:
    """Analyzes requirements to determine evaluator-optimizer workflow configuration."""

    def __init__(self):
        self.model_id = os.getenv("BEDROCK_MODEL") or "anthropic.claude-v2"
        self.parameters = {
            "temperature": 0,
            "max_tokens_to_sample": 4000
        }
        self.model = None

    def _initialize_model(self) -> None:
        """Initialize the LLM model."""
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

    def analyze_requirements(self, description: str) -> EvaluatorOptimizerAnalysis:
        """Analyze requirements and determine optimal evaluator-optimizer configuration."""
        self._initialize_model()

        # Step 1: Analyze core requirements
        core_analysis_prompt = f"""You are an expert at designing evaluator-optimizer workflows where one LLM generates solutions and another evaluates them in an iterative loop. First, analyze the core requirements:

        Requirement: {description}

        Determine:
        1. Main objective
        2. Required input data
        3. Expected final output
        4. Evaluation criteria
        5. Success metrics
        6. Iteration strategy

        Return a JSON object with this structure:
        {{
            "objective": "clear statement of the main goal",
            "inputs": ["list", "of", "required", "inputs"],
            "output": "expected final output format",
            "evaluation_criteria": [
                {{"name": "criterion_name", "description": "what to evaluate", "weight": 1.0, "required": true}}
            ],
            "success_metrics": {{"threshold": 0.8, "max_iterations": 5}},
            "iteration_strategy": "how to improve based on feedback"
        }}

        Return only the JSON object, no other text.
        """

        core_response = self.model.invoke(core_analysis_prompt)
        core_analysis = json.loads(self._extract_json(core_response))

        # Step 2: Design prompts and formats
        prompts_prompt = f"""Based on the core analysis, design the generator and evaluator prompts for the workflow.

        Core Analysis: {json.dumps(core_analysis, indent=2)}

        Design:
        1. Generator prompt template
        2. Evaluator prompt template
        3. Response formats for both
        4. Evaluation scoring system

        Return a JSON object with this structure:
        {{
            "generator_prompt": "template with placeholders",
            "evaluator_prompt": "template with placeholders",
            "output_format": {{
                "type": "object",
                "properties": {{}}
            }},
            "evaluation_format": {{
                "type": "object",
                "properties": {{}}
            }}
        }}

        Return only the JSON object, no other text.
        """

        prompts_response = self.model.invoke(prompts_prompt)
        prompts_analysis = json.loads(self._extract_json(prompts_response))

        # Step 3: Validate and combine results
        try:
            # Create evaluation criteria objects
            evaluation_criteria = [
                EvaluationCriteria(**criterion)
                for criterion in core_analysis["evaluation_criteria"]
            ]

            # Create config object
            config = EvaluatorOptimizerConfig(
                generator_prompt=prompts_analysis["generator_prompt"],
                evaluator_prompt=prompts_analysis["evaluator_prompt"],
                max_iterations=core_analysis["success_metrics"]["max_iterations"],
                success_threshold=core_analysis["success_metrics"]["threshold"],
                evaluation_criteria=evaluation_criteria,
                output_format=prompts_analysis["output_format"]
            )

            # Create analysis object
            return EvaluatorOptimizerAnalysis(
                config=config,
                input_variables=core_analysis["inputs"],
                output_variable=core_analysis["output"],
                task_description=core_analysis["objective"],
                evaluation_format=prompts_analysis["evaluation_format"]
            )

        except Exception as e:
            raise ValueError(f"Failed to parse evaluator-optimizer analysis: {str(e)}")

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling various formats."""
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
