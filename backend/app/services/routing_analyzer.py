from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import json
from langchain_aws import BedrockLLM
import boto3
import re
import os

class RouteHandler(BaseModel):
    name: str
    description: str
    prompt_template: str
    input_variables: List[str]
    output_format: Dict[str, Any]

class RoutingStep(BaseModel):
    name: str
    description: str
    classifier_prompt: str
    output_key: str
    input_variables: List[str]
    handlers: List[RouteHandler]
    output_format: Dict[str, Any] = Field(default_factory=dict)

class RoutingAnalysis(BaseModel):
    steps: List[RoutingStep]
    input_variables: List[str]
    output_variable: str

class RoutingAnalyzer:
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

    def analyze_requirements(self, description: str) -> RoutingAnalysis:
        """Analyze requirements and determine optimal routing configuration"""
        self._initialize_model()

        # Step 1: Analyze core routing requirements
        core_analysis_prompt = f"""You are an expert at designing routing workflows for LLMs. First, analyze the core requirements:

        Requirement: {description}

        Determine:
        1. Main routing objective
        2. Required input data
        3. Expected final output
        4. Categories/types of inputs to route
        5. Specialized handling needs for each category
        6. Classification criteria

        Return a JSON object with this structure:
        {{
            "objective": "clear statement of the routing goal",
            "inputs": ["list", "of", "required", "inputs"],
            "output": "expected final output format",
            "categories": ["category1", "category2", "etc"],
            "handling_needs": {{"category1": "specialized handling description"}},
            "classification_criteria": ["criteria1", "criteria2"]
        }}

        Return only the JSON object, no other text.
        """

        core_response = self.model.invoke(core_analysis_prompt)
        core_analysis = json.loads(self._extract_json(core_response))

        # Step 2: Design routing details
        routing_prompt = f"""Based on the core analysis, design detailed routing configuration.

        Core Analysis: {json.dumps(core_analysis, indent=2)}

        For the routing workflow, determine:
        1. Classification prompt for routing
        2. Specialized handlers for each category
        3. Input/output formats for each handler
        4. Validation criteria

        Return a JSON object with this structure:
        {{
            "steps": [
                {{
                    "name": "route_classifier",
                    "description": "Analyzes input and determines appropriate handler",
                    "classifier_prompt": "Prompt template for classification",
                    "output_key": "route_selection",
                    "input_variables": ["required", "inputs"],
                    "handlers": [
                        {{
                            "name": "handler_name",
                            "description": "Handler purpose",
                            "prompt_template": "Specialized prompt for this type",
                            "input_variables": ["required", "inputs"],
                            "output_format": {{
                                "type": "object",
                                "properties": {{}}
                            }}
                        }}
                    ],
                    "output_format": {{
                        "type": "object",
                        "properties": {{}}
                    }}
                }}
            ]
        }}

        Ensure:
        1. Clear classification criteria
        2. Specialized handling for each route
        3. Proper input/output formats
        4. Consistent variable naming

        Return only the JSON object, no other text.
        """

        routing_response = self.model.invoke(routing_prompt)
        routing_analysis = json.loads(self._extract_json(routing_response))

        # Step 3: Validate and combine results
        try:
            required_core_fields = {"objective", "inputs", "output", "categories"}
            if not all(field in core_analysis for field in required_core_fields):
                raise ValueError(f"Missing required core fields. Found: {set(core_analysis.keys())}")

            if "steps" not in routing_analysis:
                raise ValueError("Routing analysis missing 'steps' field")

            for step in routing_analysis["steps"]:
                step["name"] = self._normalize_identifier(step["name"])
                step["classifier_prompt"] = step["classifier_prompt"].replace("{", "{{").replace("}", "}}")

                for handler in step["handlers"]:
                    handler["name"] = self._normalize_identifier(handler["name"])
                    handler["prompt_template"] = handler["prompt_template"].replace("{", "{{").replace("}", "}}")

                required_step_fields = {
                    "name", "description", "classifier_prompt", "output_key",
                    "input_variables", "handlers", "output_format"
                }
                if not all(field in step for field in required_step_fields):
                    raise ValueError(f"Step {step.get('name', 'unknown')} missing required fields")

            return RoutingAnalysis(
                steps=[RoutingStep(**step) for step in routing_analysis["steps"]],
                input_variables=core_analysis["inputs"],
                output_variable=core_analysis["output"]
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse routing analysis: {str(e)}")

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
