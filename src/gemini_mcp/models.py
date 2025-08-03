"""Pydantic models for Gemini MCP operations"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class GeminiTask(BaseModel):
    """Individual task for Gemini execution"""
    id: str = Field(..., description="Unique task identifier")
    prompt: str = Field(..., description="Prompt for Gemini")
    model: str = Field(default="gemini-2.5-pro", description="Gemini model to use")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    result: Optional[str] = Field(default=None, description="Task result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    

class TaskBatch(BaseModel):
    """Batch of tasks for parallel execution"""
    id: str = Field(..., description="Batch identifier")
    tasks: List[GeminiTask] = Field(..., description="List of tasks")
    parallel: bool = Field(default=True, description="Execute tasks in parallel")
    

class TaskResult(BaseModel):
    """Result of task execution"""
    task_id: str
    status: TaskStatus
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class BatchResult(BaseModel):
    """Result of batch execution"""
    batch_id: str
    completed_tasks: int
    failed_tasks: int
    total_tasks: int
    results: List[TaskResult]
    total_time: float