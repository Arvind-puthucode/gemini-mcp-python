"""Gemini API client with async support"""

import asyncio
import time
from typing import Optional, Dict, Any
import google.generativeai as genai
from google.generativeai import GenerativeModel
from google.api_core import exceptions
import os
from dotenv import load_dotenv

from .models import GeminiTask, TaskResult, TaskStatus

# Load .env file from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))


class GeminiClient:
    """Async Gemini API client for parallel task execution"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable required. "
                "Please set it in your environment or create a .env file. "
                "See .env.example for reference."
            )
            
        genai.configure(api_key=self.api_key)
        self.models = {}
        
    def _get_model(self, model_name: str) -> GenerativeModel:
        """Get or create model instance"""
        if model_name not in self.models:
            self.models[model_name] = GenerativeModel(model_name)
        return self.models[model_name]
        
    async def execute_task(self, task: GeminiTask) -> TaskResult:
        """Execute a single Gemini task"""
        start_time = time.time()
        task.status = TaskStatus.RUNNING
        
        try:
            model = self._get_model(task.model)
            
            # Build prompt with context if provided
            full_prompt = task.prompt
            if task.context:
                context_str = "\n".join([f"{k}: {v}" for k, v in task.context.items()])
                full_prompt = f"{context_str}\n{task.prompt}"
            
            # Generate response
            response = await asyncio.to_thread(
                model.generate_content, full_prompt
            )
            
            result = response.text
            execution_time = time.time() - start_time
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result=result,
                execution_time=execution_time
            )
            
        except exceptions.ResourceExhausted:
            # Handle quota exceeded - fallback to flash model
            if task.model != "gemini-2.5-flash":
                task.model = "gemini-2.5-flash"
                return await self.execute_task(task)
            else:
                error_msg = "Quota exceeded for both Pro and Flash models"
                task.status = TaskStatus.FAILED
                task.error = error_msg
                return TaskResult(
                    task_id=task.id,
                    status=TaskStatus.FAILED,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            error_msg = f"Task execution failed: {str(e)}"
            task.status = TaskStatus.FAILED
            task.error = error_msg
            
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=error_msg,
                execution_time=time.time() - start_time
            )
    
    async def execute_tasks_parallel(self, tasks: list[GeminiTask], max_concurrent: int = 3) -> list[TaskResult]:
        """Execute multiple tasks in parallel with concurrency limit"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_limit(task: GeminiTask) -> TaskResult:
            async with semaphore:
                return await self.execute_task(task)
        
        # Execute all tasks concurrently with semaphore limiting
        results = await asyncio.gather(
            *[execute_with_limit(task) for task in tasks],
            return_exceptions=True
        )
        
        # Handle any exceptions that weren't caught
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(TaskResult(
                    task_id=tasks[i].id,
                    status=TaskStatus.FAILED,
                    error=str(result)
                ))
            else:
                final_results.append(result)
                
        return final_results
    
    async def execute_tasks_sequential(self, tasks: list[GeminiTask]) -> list[TaskResult]:
        """Execute tasks sequentially"""
        results = []
        for task in tasks:
            result = await self.execute_task(task)
            results.append(result)
        return results