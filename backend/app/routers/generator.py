from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
from ..services.agent_generator import AgentGenerator
from ..services.code_generator import create_code_block
from ..services.prompt_chain_generator import PromptChainGenerator
from ..services.routing_generator import RoutingGenerator
from ..services.parallelization_generator import ParallelizationGenerator
from ..services.evaluator_optimizer_generator import EvaluatorOptimizerGenerator

router = APIRouter()

class GenerateRequest(BaseModel):
    prompt: str
    framework: str

class GenerateResponse(BaseModel):
    config: Dict[str, Any]
    code: str

@router.post("/generate-code", response_model=GenerateResponse)
async def generate_code(request: GenerateRequest) -> Dict[str, Any]:
    try:
        # Handle workflow patterns
        if request.framework == "prompt_chain":
            generator = PromptChainGenerator()
            result = generator.generate(request.prompt)
            return {
                "config": result["config"],
                "code": result["code"]
            }
        elif request.framework == "routing":
            generator = RoutingGenerator()
            result = generator.generate(request.prompt)
            return {
                "config": result["config"],
                "code": result["code"]
            }
        elif request.framework == "parallelization":
            generator = ParallelizationGenerator()
            result = generator.generate(request.prompt)
            return {
                "config": result["config"],
                "code": result["code"]
            }
        elif request.framework == "evaluator_optimizer":
            generator = EvaluatorOptimizerGenerator()
            result = generator.generate(request.prompt)
            return {
                "config": result["config"],
                "code": result["code"]
            }
        elif request.framework == "lats":
            # LATS is disabled, return an error message
            raise HTTPException(status_code=400, detail="LATS framework is currently disabled")
        else:
            # Use existing framework-based generation
            agent = AgentGenerator()
            config = agent.analyze_prompt(request.prompt, request.framework)
            code = create_code_block(config, request.framework)
            return {
                "config": config,
                "code": code
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/frameworks")
async def get_frameworks() -> list:
    """Get list of available frameworks and workflow patterns"""
    return [
        {
            "id": "langgraph",
            "name": "LangGraph",
            "description": "Graph-based workflow framework"
        },
        {
            "id": "react",
            "name": "ReAct",
            "description": "Reasoning and Acting framework"
        }
    ]
