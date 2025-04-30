# AdaptFlow

A web application for generating AI agents and workflow powered by AWS Bedrock.


![AdaptFlow Demo](../AdaptFlow/assets/adaptflow.gif)

## Features

- Generate agent code using various frameworks:
  - LangGraph: Graph-based workflow framework
  - ReAct: Reasoning and Acting framework
  - LATS: Language Agent Team Search framework(coming soon)
- Interactive web interface built with React and Material-UI
- FastAPI backend with AWS Bedrock integration
- Real-time code generation with syntax highlighting
- Visual configuration viewer
- Framework-specific code generation
- Workflow patterns support:
  - Evaluator-Optimizer: Self-improving system with evaluation and feedback loops
  - Prompt Chain: Sequential steps with validation gates
  - Routing: Content-based task routing
  - Parallelization: Concurrent task processing

## Prerequisites

- Python 3.8+
- Node.js 14+
- AWS Account with Bedrock access
- AWS credentials (Access Key ID and Secret Access Key)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd agent-generator
```

2. Set up environment variables:
```bash
# Copy the example env file
cp backend/.env.example backend/.env

# Edit the .env file with your AWS credentials
nano backend/.env
```

3. Run the development servers:
```bash
# This script will:
# - Create a Python virtual environment
# - Install backend dependencies
# - Install frontend dependencies
# - Start both backend and frontend servers
./run_dev.sh
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## API Endpoints

### GET /api/frameworks
Get a list of available frameworks.

### POST /api/generate-code
Generate agent code based on the provided prompt and framework.

Request body:
```json
{
  "prompt": "string",
  "framework": "string"
}
```

## Project Structure

```
agent-generator/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── services/         # Business logic
│   │   │   ├── agent_generator.py          # Base agent generation
│   │   │   ├── code_generator.py           # Code generation utilities
│   │   │   ├── evaluator_optimizer_analyzer.py  # Evaluator-optimizer analysis
│   │   │   ├── evaluator_optimizer_generator.py # Evaluator-optimizer generation
│   │   │   ├── prompt_chain_analyzer.py    # Prompt chain analysis
│   │   │   ├── prompt_chain_generator.py   # Prompt chain generation
│   │   │   ├── routing_analyzer.py         # Routing analysis
│   │   │   ├── routing_generator.py        # Routing generation
│   │   │   ├── parallelization_analyzer.py # Parallelization analysis
│   │   │   └── parallelization_generator.py # Parallelization generation
│   │   ├── models/          # Data models
│   │   └── routers/         # API routes
│   ├── requirements.txt     # Python dependencies
│   └── run.py              # Backend server script
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── CodeDisplay.tsx    # Code display with syntax highlighting
│   │   │   └── ConfigViewer.tsx   # Configuration visualization
│   │   ├── types/          # TypeScript type definitions
│   │   │   ├── frameworks.ts      # Framework configurations
│   │   │   └── workflows.ts       # Workflow pattern types
│   │   ├── services/        # API client
│   │   └── App.tsx         # Main application
│   └── package.json        # Node.js dependencies
└── run_dev.sh             # Development startup script
```

## Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

## Workflow Patterns

### Evaluator-Optimizer
A self-improving system that uses one LLM to generate solutions and another to evaluate them in an iterative loop. Features:
- Clear evaluation criteria with weights and requirements
- Configurable success thresholds and iteration limits
- Memory of previous attempts for improvement
- Chain of thought logging

### Prompt Chain
Break down complex tasks into sequential steps with validation gates between them.

### Routing
Route tasks to specialized handlers based on content analysis.

### Parallelization
Process multiple tasks concurrently with configurable execution modes and aggregation strategies.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
