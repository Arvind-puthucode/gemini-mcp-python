"""MCP Server for Gemini orchestration"""

import asyncio
import json
import logging
from typing import Any, Sequence
import re
import sys

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

from .orchestrator import TaskOrchestrator
from .gemini_client import GeminiClient
from .models import TaskPriority

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gemini_mcp.log', mode='w'),
        logging.StreamHandler()  # Also log to console
    ]
)
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator = None


def setup_orchestrator():
    """Initialize the orchestrator"""
    global orchestrator
    try:
        client = GeminiClient()
        orchestrator = TaskOrchestrator(client, max_concurrent=3)
        logger.info("Gemini MCP Orchestrator initialized")
    except ValueError as e:
        if "GEMINI_API_KEY" in str(e):
            logger.error(f"Configuration Error: {e}")
            logger.error("Please set the GEMINI_API_KEY environment variable or create a .env file")
        else:
            logger.error(f"Failed to initialize orchestrator: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        sys.exit(1)


# Create the MCP server
server = Server("gemini-orchestrator")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="ask-gemini",
            description="Execute a single Gemini prompt",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to send to Gemini"
                    },
                    "model": {
                        "type": "string",
                        "description": "Gemini model to use (default: gemini-2.5-pro)",
                        "default": "gemini-2.5-pro"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context for the prompt",
                        "default": {}
                    }
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="parallel-ask",
            description="Execute multiple prompts in parallel",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of prompts to execute in parallel"
                    },
                    "model": {
                        "type": "string",
                        "description": "Gemini model to use (default: gemini-2.5-pro)",
                        "default": "gemini-2.5-pro"
                    },
                    "context": {
                        "type": "object",
                        "description": "Shared context for all prompts",
                        "default": {}
                    }
                },
                "required": ["prompts"]
            }
        ),
        Tool(
            name="create-code",
            description="Generate code files using Gemini with file context",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Description of what code to generate"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path where the file should be created"
                    },
                    "context_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of existing files to use as context",
                        "default": []
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language",
                        "default": "python"
                    },
                    "model": {
                        "type": "string",
                        "description": "Gemini model to use",
                        "default": "gemini-2.5-pro"
                    }
                },
                "required": ["task_description", "file_path"]
            }
        ),
        Tool(
            name="batch-status",
            description="Get status of a task batch",
            inputSchema={
                "type": "object",
                "properties": {
                    "batch_id": {
                        "type": "string",
                        "description": "ID of the batch to check"
                    }
                },
                "required": ["batch_id"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    logger.info(f"🔧 Tool called: {name} with arguments: {arguments}")
    global orchestrator
    
    if orchestrator is None:
        logger.error("❌ Orchestrator not initialized")
        return [TextContent(type="text", text="Error: Orchestrator not initialized")]
    
    try:
        if name == "ask-gemini":
            prompt = arguments["prompt"]
            model = arguments.get("model", "gemini-2.5-pro")
            context = arguments.get("context", {})
            
            result = await orchestrator.quick_ask(prompt, model, context)
            return [TextContent(type="text", text=result)]
            
        elif name == "parallel-ask":
            prompts = arguments["prompts"]
            model = arguments.get("model", "gemini-2.5-pro")
            context = arguments.get("context", {})
            
            results = await orchestrator.parallel_ask(prompts, model, context)
            
            # Format results with labels
            formatted_results = []
            for i, result in enumerate(results):
                formatted_results.append(f"**Result {i+1}:**\n{result}")
            
            combined_result = "\n\n---\n\n".join(formatted_results)
            return [TextContent(type="text", text=combined_result)]
            
        elif name == "create-code":
            logger.info(f"🔧 create-code tool called with arguments: {arguments}")
            
            # Validate required arguments
            if "task_description" not in arguments:
                return [TextContent(type="text", text="Error: task_description is required")]
            if "file_path" not in arguments:
                return [TextContent(type="text", text="Error: file_path is required")]
                
            task_desc = arguments["task_description"]
            file_path = arguments["file_path"]
            context_files = arguments.get("context_files", [])
            language = arguments.get("language", "python")
            model = arguments.get("model", "gemini-2.5-pro")

            logger.info(f"📝 Task Description: {task_desc}")
            logger.info(f"📁 File Path: {file_path}")
            logger.info(f"📄 Context Files: {context_files}")
            logger.info(f"🔤 Language: {language}")
            logger.info(f"🤖 Model: {model}")

            # Build context from files
            context = {"language": language, "target_file": file_path}

            if context_files:
                file_contents = []
                for file_path_context in context_files:
                    try:
                        with open(file_path_context, 'r') as f:
                            content = f.read()
                            file_contents.append(f"File: {file_path_context}\n```{language}\n{content}\n```")
                    except Exception as e:
                        file_contents.append(f"File: {file_path_context} (Error reading: {e})")

                context["existing_files"] = "\n\n".join(file_contents)

            # Create specialized prompt for code generation
            code_prompt = f"Generate ONLY the complete {language} code for: {task_desc}\n\nTarget file path: {file_path}\n\nRequirements:\n1. Create production-ready, well-structured code.\n2. Include proper imports and dependencies.\n3. Add comprehensive docstrings and comments.\n4. Follow {language} best practices and conventions.\n5. Ensure the code is complete and functional.\n\n{f"Context from existing files:\n{context.get('existing_files', '')}" if context_files else ""}\n\nYour response MUST contain ONLY the code, enclosed in a markdown code block (```python\n...\n```). DO NOT include any conversational text, explanations, or other markdown outside of the code block.\n"
            logger.info(f"Generated code prompt: {code_prompt}")
            result = await orchestrator.quick_ask(code_prompt, model, context)
            logger.info(f"Raw Gemini response: {result}")

            # Save the raw Gemini response to file
            try:
                import os
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                logger.info(f"💾 Attempting to write to file: {file_path}")
                logger.info(f"📏 Response length: {len(result)} characters")
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                    
                # Verify file was created
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    logger.info(f"✅ Successfully created file: {file_path} ({file_size} bytes)")
                    return [TextContent(type="text", text=f"✅ Code generated and saved to {file_path}\n\nFile size: {file_size} bytes\nContent preview:\n{result[:200]}...")]
                else:
                    logger.error(f"❌ File was not created: {file_path}")
                    return [TextContent(type="text", text=f"❌ File creation failed: {file_path}")]
                    
            except Exception as e:
                logger.error(f"❌ Error writing to file {file_path}: {e}", exc_info=True)
                return [TextContent(type="text", text=f"❌ Failed to save to {file_path}: {e}\n\nGenerated content:\n{result}")]
            
        elif name == "batch-status":
            batch_id = arguments["batch_id"]
            status = orchestrator.get_batch_status(batch_id)
            
            if status:
                status_text = json.dumps(status, indent=2)
                return [TextContent(type="text", text=f"Batch Status:\n```json\n{status_text}\n```")]
            else:
                return [TextContent(type="text", text=f"Batch {batch_id} not found")]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
    except Exception as e:
        logger.error(f"Tool execution error: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]


async def main():
    """Main entry point"""
    setup_orchestrator()
    
    # Explicitly print tools for debugging
    
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gemini-orchestrator",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())