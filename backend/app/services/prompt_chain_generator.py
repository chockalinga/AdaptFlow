from typing import Dict, Any
from .prompt_chain_analyzer import PromptChainAnalyzer

class PromptChainGenerator:
    def __init__(self):
        self.analyzer = PromptChainAnalyzer()

    def generate(self, description: str) -> Dict[str, Any]:
        """
        Generate a prompt chain implementation based on the description.
        
        Args:
            description: User's requirement description
            
        Returns:
            Dict containing:
            - config: The analyzed workflow configuration
            - code: The generated implementation code
        """
        try:
            # Analyze requirements and generate steps
            analysis = self.analyzer.analyze_requirements(description)
            
            # Generate implementation code
            code = self.analyzer.generate_code(analysis)
            
            
            # Create configuration with normalized input variables
            config = {
                "workflow_type": "prompt_chain",
                "description": description,
                "steps": [
                    {
                        **step.dict(),
                        "input_variables": [
                            var.lower().replace(" ", "_") 
                            for var in step.input_variables
                        ]
                    }
                    for step in analysis.steps
                ],
                "input_variables": [
                    var.lower().replace(" ", "_") 
                    for var in analysis.input_variables
                ],
                "output_variable": analysis.output_variable.lower().replace(" ", "_")
            }
            
            return {
                "config": config,
                "code": code
            }
            
        except Exception as e:
            raise ValueError(f"Failed to generate prompt chain: {str(e)}")
