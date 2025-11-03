"""Safe code execution engine."""

import re
import pandas as pd
from typing import Tuple, List
import signal
from contextlib import contextmanager


class SecurityError(Exception):
    """Code security violation."""
    pass


class TimeoutError(Exception):
    """Execution timeout."""
    pass


@contextmanager
def timeout_context(seconds: int):
    """Context manager for execution timeout."""
    def timeout_handler(signum, frame):
        raise TimeoutError("代码执行超时")
    
    # Set signal handler (Unix only)
    try:
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    except (AttributeError, ValueError):
        # Windows or other systems without SIGALRM - just run without timeout
        yield


class SafeCodeExecutor:
    """Safe execution of generated transformation code."""
    
    # Allowed modules
    ALLOWED_MODULES = {
        'pandas', 'pd', 're', 'datetime', 'decimal',
        'collections', 'itertools', 'functools', 'math'
    }
    
    # Forbidden patterns
    FORBIDDEN_PATTERNS = [
        r'\bimport\s+os\b', r'\bimport\s+sys\b',
        r'\bimport\s+subprocess\b', r'\b__import__\b',
        r'\beval\b', r'\bexec\b', r'\bopen\b',
        r'\bfile\b', r'__\w+__',  # Dunder methods (except allowed)
        r'\bcompile\b', r'\bglobals\b', r'\blocals\b',
    ]
    
    def validate_code(self, code: str) -> Tuple[bool, str]:
        """Validate code safety."""
        # Check forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"禁止的操作: {pattern}"
        
        # Check imports - only allow if they're in allowed modules
        import_matches = re.findall(r'^\s*import\s+(\w+)', code, re.MULTILINE)
        from_matches = re.findall(r'^\s*from\s+(\w+)', code, re.MULTILINE)
        all_imports = import_matches + from_matches
        
        for imp in all_imports:
            if imp not in self.ALLOWED_MODULES:
                return False, f"不允许的模块: {imp}"
        
        # Check required function
        if 'def transform_data(' not in code:
            return False, "缺少transform_data函数定义"
        
        return True, "代码验证通过"
    
    def execute_transformation(
        self, 
        code: str, 
        input_df: pd.DataFrame,
        timeout: int = 30
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Execute transformation code safely."""
        # Validate
        is_valid, message = self.validate_code(code)
        if not is_valid:
            raise SecurityError(message)
        
        # Build safe globals with necessary imports already loaded
        import datetime
        import decimal
        import collections
        import itertools
        import functools
        import math
        
        safe_globals = {
            '__builtins__': {
                'len': len, 'str': str, 'int': int, 'float': float,
                'bool': bool, 'list': list, 'dict': dict, 'set': set,
                'tuple': tuple, 'range': range, 'enumerate': enumerate,
                'zip': zip, 'map': map, 'filter': filter, 'sum': sum,
                'min': min, 'max': max, 'abs': abs, 'round': round,
                'sorted': sorted, 'reversed': reversed, 'all': all, 'any': any,
                'True': True, 'False': False, 'None': None,
                'print': print,  # Allow print for debugging
            },
            'pd': pd,
            're': re,
            'datetime': datetime,
            'decimal': decimal,
            'collections': collections,
            'itertools': itertools,
            'functools': functools,
            'math': math,
        }
        
        # Compile code
        try:
            compiled_code = compile(code, '<generated>', 'exec')
        except SyntaxError as e:
            raise SecurityError(f"语法错误: {e}")
        
        # Execute with timeout
        local_namespace = {}
        try:
            with timeout_context(timeout):
                exec(compiled_code, safe_globals, local_namespace)
        except TimeoutError:
            raise
        except Exception as e:
            raise SecurityError(f"执行错误: {e}")
        
        # Get transform function
        transform_func = local_namespace.get('transform_data')
        if not transform_func:
            raise SecurityError("未找到transform_data函数")
        
        # Execute transformation
        errors = []
        try:
            result_df = transform_func(input_df.copy())
            return result_df, errors
        except Exception as e:
            errors.append(f"转换错误: {str(e)}")
            return input_df, errors
