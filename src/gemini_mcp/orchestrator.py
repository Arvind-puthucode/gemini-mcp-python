"""Task orchestrator for managing Gemini execution"""

import asyncio
import time
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import GeminiTask, TaskBatch, TaskResult, BatchResult, TaskStatus, TaskPriority
from .gemini_client import GeminiClient


class TaskOrchestrator:
    """Orchestrates parallel and sequential Gemini task execution"""
    
    def __init__(self, gemini_client: GeminiClient, max_concurrent: int = 3):
        self.gemini_client = gemini_client
        self.max_concurrent = max_concurrent
        self.active_batches: Dict[str, TaskBatch] = {}
        self.completed_batches: Dict[str, BatchResult] = {}
        
    def create_task(
        self, 
        prompt: str, 
        model: str = "gemini-2.5-pro",
        priority: TaskPriority = TaskPriority.MEDIUM,
        context: Optional[Dict[str, Any]] = None
    ) -> GeminiTask:
        """Create a new Gemini task"""
        task_id = str(uuid.uuid4())[:8]
        return GeminiTask(
            id=task_id,
            prompt=prompt,
            model=model,
            priority=priority,
            context=context
        )
    
    def create_batch(self, tasks: List[GeminiTask], parallel: bool = True) -> TaskBatch:
        """Create a task batch"""
        batch_id = str(uuid.uuid4())[:8]
        batch = TaskBatch(
            id=batch_id,
            tasks=tasks,
            parallel=parallel
        )
        self.active_batches[batch_id] = batch
        return batch
    
    async def execute_batch(self, batch: TaskBatch) -> BatchResult:
        """Execute a task batch"""
        start_time = time.time()
        
        # Sort tasks by priority
        sorted_tasks = sorted(
            batch.tasks, 
            key=lambda t: list(TaskPriority).index(t.priority), 
            reverse=True
        )
        
        if batch.parallel:
            results = await self.gemini_client.execute_tasks_parallel(
                sorted_tasks, self.max_concurrent
            )
        else:
            results = await self.gemini_client.execute_tasks_sequential(sorted_tasks)
        
        # Calculate statistics
        completed = sum(1 for r in results if r.status == TaskStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == TaskStatus.FAILED)
        total_time = time.time() - start_time
        
        batch_result = BatchResult(
            batch_id=batch.id,
            completed_tasks=completed,
            failed_tasks=failed,
            total_tasks=len(results),
            results=results,
            total_time=total_time
        )
        
        # Move from active to completed
        if batch.id in self.active_batches:
            del self.active_batches[batch.id]
        self.completed_batches[batch.id] = batch_result
        
        return batch_result
    
    async def execute_single_task(self, task: GeminiTask) -> TaskResult:
        """Execute a single task"""
        return await self.gemini_client.execute_task(task)
    
    async def quick_ask(
        self, 
        prompt: str, 
        model: str = "gemini-2.5-pro",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Quick single prompt execution"""
        task = self.create_task(prompt, model, context=context)
        result = await self.execute_single_task(task)
        
        if result.status == TaskStatus.COMPLETED:
            return result.result
        else:
            raise Exception(f"Task failed: {result.error}")
    
    async def parallel_ask(
        self, 
        prompts: List[str], 
        model: str = "gemini-2.5-pro",
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Execute multiple prompts in parallel"""
        tasks = [
            self.create_task(prompt, model, context=context) 
            for prompt in prompts
        ]
        
        batch = self.create_batch(tasks, parallel=True)
        batch_result = await self.execute_batch(batch)
        
        # Return results in order, raise exception if any failed
        results = []
        for result in batch_result.results:
            if result.status == TaskStatus.COMPLETED:
                results.append(result.result)
            else:
                raise Exception(f"Task {result.task_id} failed: {result.error}")
        
        return results
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch"""
        if batch_id in self.active_batches:
            batch = self.active_batches[batch_id]
            return {
                "status": "active",
                "batch_id": batch_id,
                "total_tasks": len(batch.tasks),
                "parallel": batch.parallel
            }
        elif batch_id in self.completed_batches:
            result = self.completed_batches[batch_id]
            return {
                "status": "completed",
                "batch_id": batch_id,
                "completed_tasks": result.completed_tasks,
                "failed_tasks": result.failed_tasks,
                "total_tasks": result.total_tasks,
                "total_time": result.total_time
            }
        return None