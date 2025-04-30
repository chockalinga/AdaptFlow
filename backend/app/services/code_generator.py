from typing import Dict, Any

def create_code_block(config: Dict[str, Any], framework: str) -> str:
    if framework == "langgraph":
        return create_langgraph_code(config)
    elif framework == "react":
        return create_react_code(config)
    elif framework == "lats":
        return create_lats_code(config)
    else:
        raise ValueError("Invalid framework specified")

def create_langgraph_code(config: Dict[str, Any]) -> str:
    code = """from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from typing import Dict, List, Any, TypedDict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define state
class AgentState(TypedDict):
    messages: List[BaseMessage]
    next: str

"""
    # Generate tool definitions if needed
    if any(agent["tools"] for agent in config["agents"]):
        code += "# Define tools\n"
        tools = set()
        for agent in config["agents"]:
            tools.update(agent["tools"])
        for tool in tools:
            code += f"""class {tool.capitalize()}Tool(BaseTool):
    name = "{tool}"
    description = "Tool for {tool} operations"
    keywords = ["{tool}"]
    
    def _run(self, query: str) -> str:
        # Implement actual functionality here
        return f"Result from {tool} tool: {{query}}"
    
    async def _arun(self, query: str) -> str:
        # Implement actual functionality here
        return f"Result from {tool} tool: {{query}}"

"""
        code += "tools = [\n"
        for tool in tools:
            code += f"    {tool.capitalize()}Tool(),\n"
        code += "]\n\n"
        
        # Add ranking function for dynamic tool selection
        code += """# Ranking System for Dynamic Tool Selection
def rank_tools(query: str, tools: List[BaseTool]) -> List[BaseTool]:
    \"\"\"Ranks tools based on the frequency of their associated keywords in the query.
    Returns only tools with a positive score, sorted by score in descending order.\"\"\"
    tool_scores = {}
    for tool in tools:
        score = 0
        if hasattr(tool, 'keywords'):
            for keyword in tool.keywords:
                score += query.lower().count(keyword.lower())
        tool_scores[tool] = score
        logger.info("Tool '%s' scored %d", tool.name, score)
    ranked_tools = sorted(
        [tool for tool in tools if tool_scores.get(tool, 0) > 0],
        key=lambda t: tool_scores[t],
        reverse=True
    )
    return ranked_tools

"""
    # Generate Agent configurations
    for agent in config["agents"]:
        code += f"# Agent: {agent['name']}\n"
        code += f"def {agent['name']}_agent(state: AgentState) -> AgentState:\n"
        code += f"    \"\"\"Agent that handles {agent['role']}.\"\"\"\n"
        code += f"    llm = ChatOpenAI(model=\"{agent['model_id']}\")  # Using model_id as specified\n"
        code += "    messages = state['messages']\n"
        code += "    query_context = \" \".join([msg.content for msg in messages])\n"
        if any(agent["tools"] for agent in config["agents"]):
            code += "    relevant_tools = rank_tools(query_context, tools)\n"
            code += "    logger.info(\"Selected tools: %s\", [tool.name for tool in relevant_tools])\n"
            code += "    tool_outputs = []\n"
            code += "    for tool in relevant_tools:\n"
            code += "        try:\n"
            code += "            output = tool._run(query_context)\n"
            code += "            tool_outputs.append(output)\n"
            code += "        except Exception as e:\n"
            code += "            logger.error(\"Error in tool %s: %s\", tool.name, str(e))\n"
            code += "    if tool_outputs:\n"
            code += "        augmented_messages = messages + [AIMessage(content=\"Relevant Tool outputs: \" + \" | \".join(tool_outputs))]\n"
            code += "    else:\n"
            code += "        augmented_messages = messages\n"
        else:
            code += "    augmented_messages = messages\n"
        code += "    response = llm.invoke(augmented_messages)\n"
        code += "    return {\n"
        code += "        \"messages\": messages + [response],\n"
        code += "        \"next\": state.get(\"next\", \"\")\n"
        code += "    }\n\n"
        
    # Generate end node
    code += """def end(state: AgentState) -> AgentState:
    \"\"\"End node finalizes the workflow.\"\"\"\n
    return state

"""
    # Define routing logic
    code += """# Define routing logic
def router(state: AgentState) -> str:
    \"\"\"Route to the next node.\"\"\"\n    return state.get("next", "END")

"""
    # Generate graph configuration
    code += "# Define the graph\n"
    code += "workflow = StateGraph(AgentState)\n\n"
    
    # Add nodes
    code += "# Add nodes to the graph\n"
    for node in config["nodes"]:
        code += f"workflow.add_node(\"{node['name']}\", {node['agent']}_agent)\n"
    code += "workflow.add_node(\"end\", end)\n\n"
    
    # Add edges
    code += "# Add conditional edges\n"
    for edge in config["edges"]:
        if edge.get("condition"):
            code += f'workflow.add_edge("{edge["source"]}", "{edge["target"]}", label="{edge["condition"]}")\n'
        else:
            code += f'workflow.add_edge("{edge["source"]}", "{edge["target"]}")\n'
    
    # Set entry point
    if config["nodes"]:
        code += f"\n# Set entry point\nworkflow.set_entry_point(\"{config['nodes'][0]['name']}\")\n"
    
    # Compile and run
    code += """
# Compile the graph
app = workflow.compile()

# Run the graph
def run_agent(query: str) -> List[BaseMessage]:
    \"\"\"Run the agent on a query.\"\"\"\n    result = app.invoke({
        "messages": [HumanMessage(content=query)],
        "next": ""
    })
    return result["messages"]

if __name__ == "__main__":
    result = run_agent("Your query here")
    for message in result:
        print(f"{message.type}: {message.content}")
"""
    return code

def create_react_code(config: Dict[str, Any]) -> str:
    code = '''from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from typing import Dict, List, Any

'''
    code += "# Define tools\n"
    for tool in config.get("tools", []):
        code += f'''class {tool["name"].capitalize()}Tool(BaseTool):
    name = "{tool["name"]}"
    description = "{tool["description"]}"
    
    def _run(self, {", ".join(tool["parameters"].keys())}) -> str:
        return f"Result from {tool["name"]} tool"
    
    async def _arun(self, {", ".join(tool["parameters"].keys())}) -> str:
        return f"Result from {tool["name"]} tool"

'''
    code += "# Create tool instances\n"
    code += "tools = [\n"
    for tool in config.get("tools", []):
        code += f"    {tool['name'].capitalize()}Tool(),\n"
    code += "]\n\n"
    code += "# Define example-based ReAct prompt\n"
    examples = config.get("examples", [])
    if examples:
        code += "examples = [\n"
        for example in examples:
            code += f'''    {{
        "query": "{example["query"]}",
        "thought": "{example["thought"]}",
        "action": "{example["action"]}",
        "observation": "{example["observation"]}",
        "final_answer": "{example["final_answer"]}"
    }},
'''
        code += "]\n\n"
    if config.get("agents"):
        agent = config["agents"][0]
        code += f'''# Create ReAct agent
llm = ChatOpenAI(model="{agent['model_id']}")  # Using model_id as specified

react_prompt = ChatPromptTemplate.from_messages([
    ("system", \"\"\"You are {agent["role"]}. Your goal is to {agent["goal"]}.
    
Use the following tools to assist you:
{{tool_descriptions}}

Use the following format:
Question: The user question you need to answer
Thought: Consider what to do to best answer the question
Action: The action to take, should be one of {{tool_names}}
Action Input: The input to the action
Observation: The result of the action
... (Thought/Action/Action Input/Observation can repeat)
Thought: I now know the final answer
Final Answer: The final answer to the question\"\"\"),
    ("human", "{{input}}")
])

agent = create_react_agent(llm, tools, react_prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def run_agent(query: str) -> str:
    response = agent_executor.invoke({{"input": query}})
    return response.get("output", "No response generated")

if __name__ == "__main__":
    result = run_agent("Your query here")
    print(result)
'''
    return code

def create_lats_code(config: Dict[str, Any]) -> str:
    """Generate code for LATS agent implementation."""
    code = """from typing import Dict, List, Any
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticToolsParser
from backend.app.services.lats import LATSAgent, Reflection

# Define tools
"""
    # Generate tool definitions
    tools = []
    if config.get("tools"):
        for tool in config["tools"]:
            tool_name = tool["name"].capitalize()
            tool_desc = tool["description"]
            tool_params = tool["parameters"]
            
            # Generate tool class
            code += f"""class {tool_name}Tool(BaseTool):
    name = "{tool["name"]}"
    description = "{tool_desc}"
    
    def _run(self, **kwargs) -> str:
        \"\"\"Execute the tool functionality.
        
        Returns:
            str: Tool execution result
        \"\"\"
        # Create a list of parameter values
        result_parts = []
        for key, value in sorted(kwargs.items()):
            result_parts.append(f"{key}={value}")
        
        return f"Result from {self.name} tool: {', '.join(result_parts)}"
    
    async def _arun(self, **kwargs) -> str:
        return await self._run(**kwargs)

"""
            tools.append(tool_name)
            
    # Create tool instances
    code += "# Create tool instances\n"
    if tools:
        code += "tools = [\n"
        for tool in tools:
            code += f"    {tool}Tool(),\n"
        code += "]\n\n"
    else:
        code += "tools = []\n\n"

    # Configure LATS parameters
    workflow = config.get("workflow", {})
    code += """# Configure LATS parameters
search_config = {
    "max_iterations": %d,
    "num_candidates": 5,
    "exploration_weight": 1.0,
    "max_depth": 5,
    "consensus_threshold": %.2f
}
""" % (workflow.get("iterations", 3), workflow.get("consensus_threshold", 0.8))

    # Create reflection prompt
    code += """# Configure reflection prompt
reflection_prompt = ChatPromptTemplate.from_messages([
    ("system", \"\"\"You are an expert evaluator. Analyze the solution quality and provide a detailed reflection.
    Consider:
    1. Completeness - Does it fully address all aspects?
    2. Accuracy - Is the information correct and reliable?
    3. Relevance - Does it directly address the task?
    4. Efficiency - Is the solution well-structured and concise?
    
    Format your response as a JSON object with:
    {
        "criteria": {
            "completeness": float (0-1),
            "accuracy": float (0-1),
            "relevance": float (0-1),
            "efficiency": float (0-1)
        },
        "overall_score": float (0-1),
        "found_solution": boolean,
        "reasoning": string
    }
    \"\"\"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="candidate"),
])

"""

    # Create agent instance
    if config.get("agents"):
        agent = config["agents"][0]  # Use first agent's configuration
        code += f"""
# Initialize LATS agent
llm = ChatOpenAI(model="{agent['model_id']}")

reflection_chain = (
    reflection_prompt
    | llm.bind_tools(tools=[Reflection], tool_choice="Reflection")
    | PydanticToolsParser(tools=[Reflection])
)
agent = LATSAgent(
    llm=llm,
    tools=tools,
    reflection_chain=reflection_chain,
    config=search_config
)

def run_agent(query: str) -> Dict[str, Any]:
    \"\"\"Run the LATS agent on a query.\"\"\"
    result = agent.search(query)
    return {{
        "messages": result["messages"],
        "reflection": result["reflection"],
        "is_solved": result["is_solved"],
        "tree_height": result["tree_height"],
        "total_nodes": result["total_nodes"],
        "research": result.get("research", []),
        "critiques": result.get("critiques", []),
        "solutions": result.get("solutions", [])
    }}

if __name__ == "__main__":
    # Example usage
    query = "Your query here"
    result = run_agent(query)
    
    print("Solution found:", result["is_solved"])
    print("Tree height:", result["tree_height"])
    print("Total nodes explored:", result["total_nodes"])
    print("\\nFinal response:")
    print(result["messages"][-1].content)
    print("\\nReflection:")
    print(f"Score: {result['reflection'].overall_score}")
    print(f"Reasoning: {result['reflection'].reasoning}")
    
    if result.get("research"):
        print("\\nResearch findings:")
        for item in result["research"]:
            print(f"- {item['tool']}: {item['result']}")
            
    if result.get("critiques"):
        print("\\nCritiques:")
        for critique in result["critiques"]:
            print(f"- Solution: {critique['solution']}")
            print(f"  Critique: {critique['critique']}")
            
    if result.get("solutions"):
        print("\\nSolutions:")
        for solution in result["solutions"]:
            print(f"Iteration {solution['iteration']}: {solution['solution']}")
"""

    return code
