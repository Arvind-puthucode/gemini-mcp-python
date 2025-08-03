#!/usr/bin/env python3
"""CLI wrapper for Gemini MCP Python orchestrator"""

import argparse
import asyncio
import json
import sys
from src.gemini_mcp.gemini_client import GeminiClient
from src.gemini_mcp.orchestrator import TaskOrchestrator

async def main():
    parser = argparse.ArgumentParser(description="Gemini MCP Python Orchestrator CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Ask command
    ask_parser = subparsers.add_parser('ask', help='Single prompt execution')
    ask_parser.add_argument('prompt', help='Prompt to send to Gemini')
    ask_parser.add_argument('--model', default='gemini-2.5-pro', help='Model to use')
    
    # Parallel command
    parallel_parser = subparsers.add_parser('parallel', help='Parallel prompt execution')
    parallel_parser.add_argument('prompts', nargs='+', help='Multiple prompts to execute')
    parallel_parser.add_argument('--model', default='gemini-2.5-pro', help='Model to use')
    
    # Create-code command
    create_parser = subparsers.add_parser('create-code', help='Generate and save code')
    create_parser.add_argument('description', help='Description of code to generate')
    create_parser.add_argument('file_path', help='Path where to save the code')
    create_parser.add_argument('--language', default='python', help='Programming language')
    create_parser.add_argument('--model', default='gemini-2.5-pro', help='Model to use')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize orchestrator
        client = GeminiClient()
        orchestrator = TaskOrchestrator(client)
        
        if args.command == 'ask':
            result = await orchestrator.quick_ask(args.prompt, args.model)
            print(result)
            
        elif args.command == 'parallel':
            results = await orchestrator.parallel_ask(args.prompts, args.model)
            for i, result in enumerate(results):
                print(f"Result {i+1}: {result}")
                print("-" * 40)
                
        elif args.command == 'create-code':
            # Generate code
            code_prompt = f"Generate a complete {args.language} file for: {args.description}. Return ONLY the code, no explanations."
            generated_code = await orchestrator.quick_ask(code_prompt, args.model)
            
            # Save to file
            import os
            os.makedirs(os.path.dirname(args.file_path), exist_ok=True)
            with open(args.file_path, 'w') as f:
                f.write(generated_code)
            
            print(f"✅ Code generated and saved to: {args.file_path}")
            print(f"File size: {os.path.getsize(args.file_path)} bytes")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())