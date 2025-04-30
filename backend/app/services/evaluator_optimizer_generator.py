from typing import Dict, Any, List, Optional, Tuple
import textwrap,json
from .evaluator_optimizer_analyzer import EvaluatorOptimizerAnalyzer, EvaluatorOptimizerAnalysis

class EvaluatorOptimizerGenerator:
    def __init__(self):
        self.analyzer = EvaluatorOptimizerAnalyzer()

    def generate(self, description: str) -> Dict[str, Any]:
        """
        Generate an evaluator-optimizer workflow implementation based on the description.
        
        Args:
            description: User's requirement description
            
        Returns:
            Dict containing:
            - config: The analyzed workflow configuration
            - code: The generated implementation code
        """
        try:
            # Analyze requirements and generate configuration
            analysis = self.analyzer.analyze_requirements(description)
            
            # Generate implementation code
            code = self._generate_code(analysis)
            
            # Create configuration
            config = {
                "workflow_type": "evaluator_optimizer",
                "description": description,
                "task_description": analysis.task_description,
                "input_variables": analysis.input_variables,
                "output_variable": analysis.output_variable,
                "evaluation_criteria": [
                    criterion.dict() for criterion in analysis.config.evaluation_criteria
                ],
                "max_iterations": analysis.config.max_iterations,
                "success_threshold": analysis.config.success_threshold
            }
            
            return {
                "config": config,
                "code": code
            }
            
        except Exception as e:
            raise ValueError(f"Failed to generate evaluator-optimizer workflow: {str(e)}")

    def _generate_code(self, analysis: EvaluatorOptimizerAnalysis) -> str:

        # 1. Prepare dynamic pieces
        inputs_list     = ", ".join(f'"{v}"' for v in analysis.input_variables)
        output_key      = analysis.output_variable.strip().lower().replace(" ", "_")
        max_iters       = analysis.config.max_iterations
        threshold       = analysis.config.success_threshold
        task_desc       = analysis.task_description.replace('"', '\\"')

        # Embed your output_format and evaluation_format as JSON
        output_fmt_json = json.dumps(analysis.config.output_format, indent=4)
        eval_fmt_json   = json.dumps(analysis.evaluation_format, indent=4)

        # Build the literal prompts with formats appended
        gen_prompt = (
            analysis.config.generator_prompt.strip()
            + "\\n\\nOutput format:\\n"
            + output_fmt_json
        )
        eval_prompt = (
            analysis.config.evaluator_prompt.strip()
            + "\\n\\nEvaluation format:\\n"
            + eval_fmt_json
        )

        # 2. (Optional) If you prefer to keep model/LLM params in config, add them there.
        #    Otherwise we fall back to these defaults:
        model_name  = "bedrock/anthropic.claude-v2"
        max_tokens  = 4096
        temperature = 0.7

        # 3. The raw script template
        template = f"""
        from typing import Dict, Any, List
        import asyncio
        import json
        import logging
        from tenacity import retry, stop_after_attempt, wait_exponential
        from litellm import completion
        import xml.etree.ElementTree as ET

        # ——————————— YOUR CONFIG ———————————
        MODEL_NAME        = "{model_name}"
        MAX_TOKENS        = {max_tokens}
        TEMPERATURE       = {temperature}
        MAX_ITERATIONS    = {max_iters}
        SUCCESS_THRESHOLD = {threshold}

        GENERATOR_PROMPT = {json.dumps(gen_prompt)}
        EVALUATOR_PROMPT = {json.dumps(eval_prompt)}

        # ——————————— SETUP ———————————
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1,max=5))
        def llm_call(prompt: str, system_prompt: str = "") -> str:
            msgs = ([{{"role":"system","content":system_prompt}}] if system_prompt else []) \
                + [{{"role":"user","content":prompt}}]
            resp = completion(
                model=MODEL_NAME,
                messages=msgs,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            return resp.choices[0].message.content

        def extract_xml(text: str, tag: str) -> str:
            try:
                root = ET.fromstring(f"<root>{{text}}</root>")
                el = root.find(tag)
                return el.text.strip() if el is not None and el.text else ""
            except Exception as e:
                raise RuntimeError(f"Failed to parse <{{tag}}> from LLM response: {{e}}")

        async def generate(task: str, context: str = "") -> Dict[str,str]:
            payload = GENERATOR_PROMPT + f"\\nTask: {{task}}" \
                    + (f"\\nContext:\\n{{context}}" if context else "")
            raw = llm_call(payload)
            return {{
                "thoughts": extract_xml(raw, "thoughts"),
                "response": extract_xml(raw, "response")
            }}

        async def evaluate(content: str, task: str) -> Dict[str,Any]:
            payload = EVALUATOR_PROMPT \
                    + f"\\nOriginal task: {{task}}" \
                    + f"\\nContent to evaluate: {{content}}"
            raw = llm_call(payload)
            score = float(extract_xml(raw, "evaluation_score") or 0.0)
            return {{
                "score": score,
                "feedback": extract_xml(raw, "feedback")
            }}

        async def run_workflow(task: str) -> Dict[str,Any]:
            \"\"\"Generate sub-reports in parallel, then iteratively refine.\"\"\"
            sources = [{inputs_list}]

            # Initial parallel pass
            initial = await asyncio.gather(*[
                generate(f"{{task}} for '{{src}}'", "")
                for src in sources
            ])
            memory = {{src: out["response"] for src, out in zip(sources, initial)}}
            combined = "\\n\\n".join(f"## {{src}}\\n{{resp}}" for src, resp in memory.items())

            # Iterative evaluation & refinement
            for i in range(MAX_ITERATIONS):
                ev = await evaluate(combined, task)
                logger.info(f"Iteration {{i+1}} → score={{ev['score']}}")
                if ev["score"] >= SUCCESS_THRESHOLD:
                    return {{
                        "success": True,
                        "iterations": i+1,
                        "final_{output_key}": combined,
                        "feedback": ev["feedback"]
                    }}
                # regenerate with feedback
                ctx = "Previous combined report:\\n" + combined \
                    + f"\\n\\nEvaluator feedback: {{ev['feedback']}}"
                refined = await asyncio.gather(*[
                    generate(f"{{task}} for '{{src}}'", ctx)
                    for src in sources
                ])
                memory = {{src: out["response"] for src, out in zip(sources, refined)}}
                combined = "\\n\\n".join(f"## {{src}}\\n{{resp}}" for src, resp in memory.items())

            return {{
                "success": False,
                "iterations": MAX_ITERATIONS,
                "final_{output_key}": combined
            }}

        if __name__ == "__main__":
            task = "{analysis.task_description}"
            result = asyncio.run(run_workflow(task))
            print(json.dumps(result, indent=2))
        """

        # 4. Dedent and return the complete script
        return textwrap.dedent(template)



    

