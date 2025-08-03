# Gemini MCP Python

A Python-based MCP server and cli tool for Gemini API orchestration, designed for AI-driven development workflows from other LLMs like Claude Code.

## Features

- **Parallel Task Execution**: Execute multiple Gemini prompts concurrently with configurable limits
- **Orchestration-First Design**: Built specifically for orchestrating AI agents and managing complex workflows
- **Smart Fallbacks**: Automatic fallback from Pro to Flash models when quota is exceeded
- **Code Generation**: Specialized tool for generating code files with context awareness
- **Batch Management**: Create and monitor task batches with real-time status updates
- **MCP Integration**: Seamless integration with Claude Code and other MCP clients

## Installation

```bash
cd gemini-mcp-python
pip install -e .
```

## Configuration

**Required:** Set your Gemini API key before using the MCP server.

### Option 1: Environment Variable
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Option 2: .env File (Recommended)
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your actual API key
# GEMINI_API_KEY=your-actual-api-key-here
```

### Get Your API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy and use it in your configuration

**⚠️ Important:** The MCP server will not start without a valid API key.

## Claude Code Integration

Add to your Claude Code MCP configuration (`~/.claude.json`):

```json
{
  "mcpServers": {
    "gemini-orchestrator": {
      "command": "python",
      "args": ["-m", "gemini_mcp.server"],
      "cwd": "/path/to/gemini-mcp-python" # Replace with the actual absolute path to your gemini-mcp-python directory
    }
  }
}
```

## Available Tools

### 🔧 MCP Integration (via Claude Code)
When Claude Code MCP is properly connected:

#### ask-gemini
```bash
/gemini-orchestrator:ask-gemini prompt:"Your prompt here" model:"gemini-2.5-pro"
```

#### parallel-ask  
```bash
/gemini-orchestrator:parallel-ask prompts:["Prompt 1", "Prompt 2", "Prompt 3"]
```

#### create-code
```bash
/gemini-orchestrator:create-code task_description:"Create FastAPI app" file_path:"app.py" context_files:["models.py"]
```

#### batch-status
```bash
/gemini-orchestrator:batch-status batch_id:"abc123"
```

### 🖥️ CLI Wrapper (Always Available)
Direct command-line access:

#### Single prompt
```bash
python cli_orchestrator.py ask "What is the capital of France?"
```

#### Parallel prompts
```bash
python cli_orchestrator.py parallel "What is 2+2?" "What color is grass?" "Name a planet"
```

#### Generate code files
```bash
python cli_orchestrator.py create-code "A fibonacci function" "fibonacci.py" --language python
```



## Architecture

- **TaskOrchestrator**: Manages parallel execution and prioritization
- **GeminiClient**: Async Gemini API client with error handling
- **MCP Server**: Tool interface for Claude Code integration
- **Models**: Pydantic models for type safety and validation

## Development

A comprehensive test suite is available to ensure reliability and can be run with `pytest`.

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff src/
```

## License

MIT