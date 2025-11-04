"""Normalization service layer."""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from invitation.ai_normalization_service import AINormalizationService, LLMService
from web.services.code_executor import SafeCodeExecutor, SecurityError
from web.services.task_repository import TaskRepository


class NormalizationService:
    """Business logic for normalization tasks."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize LLM service
        self.llm_service = LLMService(
            api_key=config.get('API_KEY'),
            model=config.get('MODEL_NAME', 'gpt-4o'),
            base_url=config.get('API_BASE_URL')
        )
        
        # Initialize AI normalization service
        self.ai_service = AINormalizationService(llm_service=self.llm_service)
        
        # Initialize code executor
        self.code_executor = SafeCodeExecutor()
    
    def create_task(self, task_repo: TaskRepository, filename: str, 
                   file_path: Path) -> dict:
        """Create a new normalization task."""
        # Analyze CSV
        analysis = self.ai_service.analyze_csv(file_path)
        
        # Convert dtypes to JSON-serializable format
        if 'dtypes' in analysis:
            analysis['dtypes'] = {k: str(v) for k, v in analysis['dtypes'].items()}
        
        # Convert null_counts to int (pandas returns numpy int64)
        if 'null_counts' in analysis:
            analysis['null_counts'] = {k: int(v) for k, v in analysis['null_counts'].items()}
        
        # Create task
        task = task_repo.create_task(filename, file_path, analysis)
        
        # Generate initial rule suggestion
        initial_suggestion = self._generate_initial_suggestion(analysis)
        
        # Add to conversation
        task['conversation'].append({
            'role': 'system',
            'content': initial_suggestion,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        # Generate initial code and preview
        task['rule_draft'] = {
            'description': initial_suggestion,
            'code': self._generate_initial_code(analysis),
            'version': 1
        }
        
        # Generate preview
        task['preview'] = self._generate_preview(task)
        task['status'] = 'interactive'
        
        # Save task
        task['initial_suggestion'] = initial_suggestion
        task_repo.save_task(task)
        
        return task
    
    def _generate_initial_suggestion(self, analysis: dict) -> str:
        """Generate initial rule suggestion based on CSV analysis."""
        columns = analysis.get('columns', [])
        
        # Check for standard columns
        standard_cols = {'Mail', 'Team', 'Organization'}
        existing_cols = set(columns)
        
        if standard_cols.issubset(existing_cols):
            return f"检测到标准列格式。CSV包含{len(columns)}列，{analysis.get('row_count', 0)}行数据。可以直接使用或进行进一步调整。"
        
        # Suggest mappings
        suggestions = []
        for col in columns:
            col_lower = col.lower()
            if 'email' in col_lower or 'mail' in col_lower:
                if col != 'Mail':
                    suggestions.append(f"列'{col}'可能需要重命名为'Mail'")
            elif 'team' in col_lower or 'group' in col_lower or 'dept' in col_lower:
                if col != 'Team':
                    suggestions.append(f"列'{col}'可能需要重命名为'Team'")
            elif 'org' in col_lower or 'company' in col_lower:
                if col != 'Organization':
                    suggestions.append(f"列'{col}'可能需要重命名为'Organization'")
        
        if suggestions:
            return "初始规则建议：\n" + "\n".join(suggestions) + "\n\n您可以使用自然语言描述需要的转换规则。"
        
        return f"已分析CSV文件：{len(columns)}列，{analysis.get('row_count', 0)}行。请描述您需要的标准化规则。"
    
    def _generate_initial_code(self, analysis: dict) -> str:
        """Generate initial transformation code."""
        columns = analysis.get('columns', [])
        
        # Build a simple initial transform that passes through data
        # Note: pd is already in global scope, no need to import
        code_lines = [
            "def transform_data(df):",
            "    result_df = df.copy()",
            ""
        ]
        
        # Add standard column mappings if detected
        for col in columns:
            col_lower = col.lower()
            if 'email' in col_lower or 'mail' in col_lower:
                if col != 'Mail':
                    code_lines.append(f"    result_df['Mail'] = result_df['{col}']")
            elif 'team' in col_lower or 'group' in col_lower or 'dept' in col_lower:
                if col != 'Team':
                    code_lines.append(f"    result_df['Team'] = result_df['{col}']")
            elif 'org' in col_lower or 'company' in col_lower:
                if col != 'Organization':
                    code_lines.append(f"    result_df['Organization'] = result_df['{col}']")
        
        code_lines.extend([
            "",
            "    return result_df"
        ])
        
        return "\n".join(code_lines)
    
    def _generate_preview(self, task: dict, limit: int = 20) -> dict:
        """Generate preview by executing code on first N rows."""
        try:
            file_path = Path(task['original_file']['path'])
            code = task['rule_draft']['code']
            
            # Load first N rows
            df = pd.read_csv(file_path, nrows=limit + 5)
            
            # Execute transformation
            result_df, errors = self.code_executor.execute_transformation(code, df)
            
            # Convert to list of dicts
            preview_rows = result_df.head(limit).to_dict(orient='records')
            
            return {
                'rows': preview_rows,
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'errors': errors
            }
        except Exception as e:
            return {
                'rows': [],
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'errors': [f"预览生成失败: {str(e)}"]
            }
    
    def process_chat(self, task_repo: TaskRepository, task: dict, 
                    user_message: str) -> dict:
        """Process a chat message and update rules."""
        # Add user message to conversation
        task['conversation'].append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        # Generate updated rule using LLM
        try:
            # Build context for LLM
            columns = task['analysis'].get('columns', [])
            current_code = task.get('rule_draft', {}).get('code', '')
            
            # Call LLM to update code
            updated_code = self._call_llm_for_code_update(
                user_message, columns, current_code
            )
            
            # Validate and update rule draft
            is_valid, msg = self.code_executor.validate_code(updated_code)
            if not is_valid:
                raise SecurityError(msg)
            
            updated_description = f"已应用规则: {user_message}"
            
            task['rule_draft'] = {
                'description': updated_description,
                'code': updated_code,
                'version': task.get('rule_draft', {}).get('version', 0) + 1
            }
            
            # Generate new preview
            task['preview'] = self._generate_preview(task)
            
            # Add assistant response
            task['conversation'].append({
                'role': 'assistant',
                'content': updated_description,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
            
        except Exception as e:
            error_msg = f"规则更新失败: {str(e)}"
            task['conversation'].append({
                'role': 'assistant',
                'content': error_msg,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
        
        # Save task
        task_repo.save_task(task)
        
        return task
    
    def _call_llm_for_code_update(self, user_message: str, columns: list, 
                                  current_code: str) -> str:
        """Call LLM to generate updated transformation code."""
        # For now, implement a simple rule-based approach
        # In production, this would call the LLM service
        
        # Parse user intent
        message_lower = user_message.lower()
        
        # Start with current code or basic template
        if current_code:
            code_lines = current_code.split('\n')
        else:
            code_lines = [
                "def transform_data(df):",
                "    result_df = df.copy()",
            ]
        
        # Add transformation based on user message
        new_transforms = []
        
        # Handle lowercase conversion
        if 'lowercase' in message_lower or '小写' in message_lower or 'lower' in message_lower:
            for col in columns:
                if 'mail' in col.lower() or 'email' in col.lower():
                    new_transforms.append(f"    result_df['{col}'] = result_df['{col}'].str.lower()")
        
        # Handle strip/trim
        if 'strip' in message_lower or 'trim' in message_lower or '去除空格' in message_lower or '空格' in message_lower:
            for col in columns:
                if 'mail' in col.lower() or 'email' in col.lower() or 'name' in col.lower():
                    new_transforms.append(f"    result_df['{col}'] = result_df['{col}'].str.strip()")
        
        # Insert new transforms before the return statement
        if new_transforms:
            # Find return statement
            return_idx = -1
            for i, line in enumerate(code_lines):
                if 'return' in line:
                    return_idx = i
                    break
            
            if return_idx > 0:
                code_lines = code_lines[:return_idx] + new_transforms + code_lines[return_idx:]
            else:
                code_lines.extend(new_transforms + ["", "    return result_df"])
        
        return "\n".join(code_lines)
    
    def apply_transformation(self, task_repo: TaskRepository, task: dict) -> dict:
        """Apply transformation to full dataset."""
        try:
            file_path = Path(task['original_file']['path'])
            code = task['rule_draft']['code']
            
            # Load full CSV
            df = pd.read_csv(file_path)
            total_rows = len(df)
            
            # Execute transformation
            result_df, errors = self.code_executor.execute_transformation(code, df)
            
            # Save results
            runtime_dir = Path(self.config['RUNTIME_DIR'])
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            original_name = Path(task['original_file']['filename']).stem
            
            output_path = runtime_dir / 'results' / f"normalized_{original_name}_{timestamp}.csv"
            result_df.to_csv(output_path, index=False)
            
            # Save errors if any
            error_path = None
            error_rows = len(errors)
            if errors:
                error_path = runtime_dir / 'results' / f"errors_{task['task_id']}.csv"
                error_df = pd.DataFrame({'error': errors})
                error_df.to_csv(error_path, index=False)
            
            # Update task
            task['result'] = {
                'output_path': str(output_path),
                'error_path': str(error_path) if error_path else None,
                'stats': {
                    'total_rows': total_rows,
                    'success_rows': total_rows - error_rows,
                    'error_rows': error_rows
                }
            }
            task['status'] = 'applied'
            
            task_repo.save_task(task)
            
            return task['result']
            
        except Exception as e:
            raise Exception(f"执行标准化失败: {str(e)}")
