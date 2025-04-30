from typing import Dict, Any, Optional
import os
import json
import re
import boto3
from langchain_aws import BedrockLLM

class AgentGenerator:
    def __init__(self):
        # Use Bedrock model (defaulting to anthropic.claude-v2; can be overridden via BEDROCK_MODEL)
        self.model_id = os.getenv("BEDROCK_MODEL") or "anthropic.claude-v2"
        # Bedrock-specific parameters
        self.parameters = {
            "temperature": 0,
            "max_tokens_to_sample": 2000
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

    @staticmethod
    def extract_json(response_text: str) -> dict:
        match = re.search(r"({.*})", response_text, flags=re.DOTALL)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        else:
            raise ValueError("No valid JSON block found in the response.")

    def analyze_prompt(self, user_prompt: str, framework: str, refine: bool = True) -> Dict[str, Any]:
        self._initialize_model()
        system_prompt = self._get_system_prompt_for_framework(framework)
        try:
            formatted_prompt = f"""<|begin_of_text|>
<|system|>
{system_prompt}
<|user|>
{user_prompt}
<|assistant|>
"""
            response = self.model.invoke(formatted_prompt)
            initial_config = self.extract_json(response)
            
            return initial_config
        except Exception as e:
            raise ValueError(f"Error in analyzing prompt: {str(e)}")

    def _get_system_prompt_for_framework(self, framework: str) -> str:
        if framework == "langgraph":
            return """
            You are an expert at creating AI agents using LangChain's LangGraph framework. Based on the user's request,
            suggest appropriate agents, their roles, tools, and nodes for the graph. Include an explicit end node.
            Format your response as JSON with this structure:
            {
                "agents": [
                    {
                        "name": "agent_name",
                        "role": "role description",
                        "goal": "clear goal",
                        "tools": ["tool1", "tool2"],
                        "model_id": "model name (e.g., gpt-4)"
                    }
                ],
                "nodes": [
                    {
                        "name": "node_name",
                        "description": "detailed description",
                        "agent": "agent_name"
                    }
                ],
                "edges": [
                    {
                        "source": "source node",
                        "target": "target node or END",
                        "condition": "optional condition description"
                    }
                ]
            }
            """
        elif framework == "react":
            return """
            You are an expert at creating AI agents using the ReAct (Reasoning + Acting) framework. Based on the user's request,
            suggest appropriate agents, their roles, tools, and specific reasoning steps. Format your response as JSON with this structure:
            {
                "agents": [
                    {
                        "name": "agent name",
                        "role": "specific role description",
                        "goal": "clear goal",
                        "tools": ["tool1", "tool2"],
                        "model_id": "model name (e.g., gpt-4)"
                    }
                ],
                "tools": [
                    {
                        "name": "tool name",
                        "description": "detailed description of what the tool does",
                        "parameters": {
                            "param1": "parameter description",
                            "param2": "parameter description"
                        }
                    }
                ],
                "examples": [
                    {
                        "query": "example user query",
                        "thought": "example thought process",
                        "action": "example action to take",
                        "observation": "example observation",
                        "final_answer": "example final answer"
                    }
                ]
            }
            """
        elif framework == "lats":
            return """
            You are an expert at creating AI agents using the LATS (Language Agent Team Search) framework. Based on the user's request,
            suggest a team of specialized agents working together to solve complex tasks. Format your response as a valid JSON object with this structure:

            {
                "agents": [
                    {
                        "name": "researcher",
                        "role": "Research and information gathering",
                        "goal": "Break down problems and gather relevant information",
                        "tools": ["search", "analyze", "summarize"],
                        "model_id": "gpt-4",
                        "description": "Detailed description of agent's responsibilities and approach"
                    }
                ],
                "workflow": {
                    "phases": {
                        "research": {
                            "description": "Gather and analyze information",
                            "required_tools": ["search", "analyze"],
                            "success_criteria": "Sufficient relevant information gathered"
                        },
                        "critique": {
                            "description": "Evaluate proposed solutions",
                            "required_tools": ["evaluate"],
                            "success_criteria": "Solution quality meets threshold"
                        },
                        "solve": {
                            "description": "Implement final solution",
                            "required_tools": ["implement"],
                            "success_criteria": "Solution successfully implemented"
                        }
                    },
                    "iterations": 3,
                    "consensus_threshold": 0.8,
                    "max_depth": 5
                },
                "tools": [
                    {
                        "name": "search",
                        "description": "Search for relevant information",
                        "parameters": {
                            "query": {
                                "type": "string",
                                "description": "Search query to execute",
                                "required": true
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "required": false,
                                "default": 5
                            }
                        }
                    },
                    {
                        "name": "analyze",
                        "description": "Analyze gathered information",
                        "parameters": {
                            "content": {
                                "type": "string",
                                "description": "Content to analyze",
                                "required": true
                            },
                            "criteria": {
                                "type": "array",
                                "description": "Analysis criteria",
                                "required": false,
                                "default": ["relevance", "accuracy", "completeness"]
                            }
                        }
                    },
                    {
                        "name": "evaluate",
                        "description": "Evaluate proposed solutions",
                        "parameters": {
                            "solution": {
                                "type": "string",
                                "description": "Solution to evaluate",
                                "required": true
                            },
                            "metrics": {
                                "type": "array",
                                "description": "Evaluation metrics",
                                "required": false,
                                "default": ["effectiveness", "efficiency", "feasibility"]
                            }
                        }
                    }
                ]
            }

            Key requirements:
            1. Each tool parameter must specify its type, description, and whether it's required
            2. Each workflow phase must include a description and success criteria
            3. Agent descriptions should detail their specific responsibilities
            4. Tool descriptions should be clear and specific about their functionality
            5. Parameters should include sensible defaults for optional fields

            Ensure your response is a properly formatted JSON object that matches this structure exactly.
            """
        else:
            raise ValueError(f"Unsupported framework: {framework}")

    def _get_default_config(self, framework: str) -> Dict[str, Any]:
        if framework == "langgraph":
            return {
                "agents": [
                    {
                        "name": "default_assistant",
                        "role": "General Assistant",
                        "goal": "Help with basic tasks",
                        "tools": ["basic_tool"],
                        "model_id": "gpt-4",
                    }
                ],
                "nodes": [
                    {
                        "name": "process_input",
                        "description": "Process user input",
                        "agent": "default_assistant",
                    }
                ],
                "edges": [
                    {
                        "source": "process_input",
                        "target": "END"
                    }
                ],
            }
        elif framework == "react":
            return {
                "agents": [
                    {
                        "name": "default_assistant",
                        "role": "General Assistant",
                        "goal": "Help with basic tasks",
                        "tools": ["basic_tool"],
                        "model_id": "gpt-4",
                    }
                ],
                "tools": [
                    {
                        "name": "basic_tool",
                        "description": "A basic utility tool",
                        "parameters": {"input": "User input to process"},
                    }
                ],
                "examples": [
                    {
                        "query": "Help me find information",
                        "thought": "I need to search for relevant information",
                        "action": "Use search tool",
                        "observation": "Found relevant results",
                        "final_answer": "Here is the information you requested",
                    }
                ],
            }
        elif framework == "lats":
            return {
                "agents": [
                    {
                        "name": "researcher",
                        "role": "Research and information gathering",
                        "goal": "Break down problems and gather relevant information",
                        "tools": ["search", "analyze", "summarize"],
                        "model_id": "gpt-4"
                    },
                    {
                        "name": "critic",
                        "role": "Solution evaluation",
                        "goal": "Review and improve proposed solutions",
                        "tools": ["evaluate", "suggest_improvements"],
                        "model_id": "gpt-4"
                    },
                    {
                        "name": "solver",
                        "role": "Solution implementation",
                        "goal": "Implement solutions based on research and feedback",
                        "tools": ["implement", "test", "refine"],
                        "model_id": "gpt-4"
                    }
                ],
                "workflow": {
                    "phases": ["research", "critique", "solve"],
                    "iterations": 3,
                    "consensus_threshold": 0.8
                },
                "tools": [
                    {
                        "name": "search",
                        "description": "Search for relevant information",
                        "parameters": {"query": "Search query to execute"}
                    },
                    {
                        "name": "analyze",
                        "description": "Analyze gathered information",
                        "parameters": {"content": "Content to analyze"}
                    },
                    {
                        "name": "evaluate",
                        "description": "Evaluate proposed solutions",
                        "parameters": {"solution": "Solution to evaluate"}
                    }
                ]
            }
        else:
            return {}
