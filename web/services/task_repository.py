"""Task persistence layer."""

import json
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime


class TaskRepository:
    """Manages task persistence using JSON files."""
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.tasks_dir = self.base_path / 'tasks'
        self.uploads_dir = self.base_path / 'uploads'
        self.results_dir = self.base_path / 'results'
        
        # Ensure directories exist
        for dir_path in [self.tasks_dir, self.uploads_dir, self.results_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def create_task(self, original_filename: str, file_path: Path, 
                   analysis: dict) -> dict:
        """Create a new task."""
        task_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + 'Z'
        
        task = {
            'task_id': task_id,
            'status': 'pending',  # pending -> interactive -> applied
            'created_at': now,
            'updated_at': now,
            'original_file': {
                'filename': original_filename,
                'path': str(file_path),
                'size': file_path.stat().st_size
            },
            'analysis': analysis,
            'conversation': [],
            'rule_draft': None,
            'preview': None,
            'result': None
        }
        
        self.save_task(task)
        return task
    
    def save_task(self, task: dict) -> None:
        """Save task with atomic write."""
        task['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        task_file = self.tasks_dir / f"{task['task_id']}.json"
        temp_file = task_file.with_suffix('.json.tmp')
        
        # Write to temp file
        with temp_file.open('w', encoding='utf-8') as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
        
        # Atomic replace
        temp_file.replace(task_file)
    
    def load_task(self, task_id: str) -> Optional[dict]:
        """Load task by ID."""
        task_file = self.tasks_dir / f"{task_id}.json"
        if not task_file.exists():
            return None
        
        with task_file.open('r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_tasks(self, limit: int = 20) -> list[dict]:
        """List recent tasks."""
        task_files = sorted(
            self.tasks_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]
        
        tasks = []
        for task_file in task_files:
            if not task_file.name.endswith('.tmp'):
                with task_file.open('r', encoding='utf-8') as f:
                    tasks.append(json.load(f))
        
        return tasks
