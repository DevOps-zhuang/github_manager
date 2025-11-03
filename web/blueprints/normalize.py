"""Normalization blueprint."""

from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid
from datetime import datetime

from web.services.task_repository import TaskRepository
from web.services.normalization_service import NormalizationService
from web.middleware.auth_middleware import require_auth

normalize_bp = Blueprint('normalize', __name__)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@normalize_bp.route('/tasks', methods=['POST'])
@require_auth
def create_task():
    """Upload CSV and create normalization task."""
    # Check file in request
    if 'file' not in request.files:
        return jsonify({'error': '未提供文件', 'code': 'NO_FILE'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '文件名为空', 'code': 'EMPTY_FILENAME'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型', 'code': 'INVALID_FILE_TYPE'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    runtime_dir = Path(current_app.config['RUNTIME_DIR'])
    temp_id = str(uuid.uuid4())
    upload_path = runtime_dir / 'uploads' / f"{temp_id}_{filename}"
    file.save(upload_path)
    
    # Create task
    try:
        task_repo = TaskRepository(runtime_dir)
        norm_service = NormalizationService(current_app.config)
        
        # Analyze and create task
        task = norm_service.create_task(task_repo, filename, upload_path)
        
        return jsonify({
            'task_id': task['task_id'],
            'analysis': task['analysis'],
            'initial_suggestion': task.get('initial_suggestion', ''),
            'preview': task.get('preview', {}).get('rows', [])
        }), 201
    except Exception as e:
        current_app.logger.error(f"Task creation failed: {e}", exc_info=True)
        return jsonify({'error': '任务创建失败', 'code': 'TASK_CREATE_ERROR'}), 500


@normalize_bp.route('/tasks/<task_id>', methods=['GET'])
@require_auth
def get_task(task_id):
    """Get task details."""
    runtime_dir = Path(current_app.config['RUNTIME_DIR'])
    task_repo = TaskRepository(runtime_dir)
    task = task_repo.load_task(task_id)
    
    if not task:
        return jsonify({'error': '任务不存在', 'code': 'TASK_NOT_FOUND'}), 404
    
    return jsonify({
        'task_id': task['task_id'],
        'status': task['status'],
        'rule_draft': task.get('rule_draft'),
        'preview': task.get('preview'),
        'conversation': task.get('conversation', [])[-6:],  # Recent 6 messages
        'result': task.get('result')
    }), 200


@normalize_bp.route('/tasks/<task_id>/chat', methods=['POST'])
@require_auth
def chat(task_id):
    """Multi-turn conversation for rule refinement."""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空', 'code': 'EMPTY_BODY'}), 400
    
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': '消息不能为空', 'code': 'EMPTY_MESSAGE'}), 400
    
    # Load task
    runtime_dir = Path(current_app.config['RUNTIME_DIR'])
    task_repo = TaskRepository(runtime_dir)
    task = task_repo.load_task(task_id)
    
    if not task:
        return jsonify({'error': '任务不存在', 'code': 'TASK_NOT_FOUND'}), 404
    
    if task['status'] == 'applied':
        return jsonify({'error': '任务已锁定', 'code': 'TASK_LOCKED'}), 400
    
    try:
        norm_service = NormalizationService(current_app.config)
        updated_task = norm_service.process_chat(task_repo, task, user_message)
        
        return jsonify({
            'updated_rule': updated_task['rule_draft'],
            'preview': updated_task.get('preview', {}).get('rows', []),
            'conversation': updated_task['conversation'][-6:]  # Return recent 6 messages
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Chat processing failed: {e}", exc_info=True)
        return jsonify({'error': '对话处理失败', 'code': 'CHAT_ERROR'}), 500


@normalize_bp.route('/tasks/<task_id>/apply', methods=['POST'])
@require_auth
def apply_task(task_id):
    """Apply transformation to full dataset."""
    runtime_dir = Path(current_app.config['RUNTIME_DIR'])
    task_repo = TaskRepository(runtime_dir)
    task = task_repo.load_task(task_id)
    
    if not task:
        return jsonify({'error': '任务不存在', 'code': 'TASK_NOT_FOUND'}), 404
    
    if task['status'] == 'applied':
        return jsonify({'error': '任务已执行', 'code': 'ALREADY_APPLIED'}), 400
    
    try:
        norm_service = NormalizationService(current_app.config)
        result = norm_service.apply_transformation(task_repo, task)
        
        return jsonify({
            'status': 'applied',
            'stats': result.get('stats', {})
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Apply failed: {e}", exc_info=True)
        return jsonify({'error': '执行失败', 'code': 'APPLY_ERROR'}), 500


@normalize_bp.route('/tasks/<task_id>/download', methods=['GET'])
@require_auth
def download_result(task_id):
    """Download normalized result file."""
    runtime_dir = Path(current_app.config['RUNTIME_DIR'])
    task_repo = TaskRepository(runtime_dir)
    task = task_repo.load_task(task_id)
    
    if not task:
        return jsonify({'error': '任务不存在', 'code': 'TASK_NOT_FOUND'}), 404
    
    if task['status'] != 'applied':
        return jsonify({'error': '结果未就绪', 'code': 'RESULT_NOT_READY'}), 400
    
    result = task.get('result')
    if not result or not result.get('output_path'):
        return jsonify({'error': '结果文件不存在', 'code': 'NO_RESULT_FILE'}), 404
    
    # Resolve path - could be relative or absolute
    output_path = Path(result['output_path'])
    if not output_path.is_absolute():
        # Make it absolute relative to project root
        output_path = Path.cwd() / output_path
    
    if not output_path.exists():
        return jsonify({'error': '结果文件不存在', 'code': 'FILE_NOT_FOUND'}), 404
    
    return send_file(output_path, as_attachment=True, download_name=output_path.name)


@normalize_bp.route('/tasks/<task_id>/errors', methods=['GET'])
@require_auth
def download_errors(task_id):
    """Download error rows file."""
    runtime_dir = Path(current_app.config['RUNTIME_DIR'])
    task_repo = TaskRepository(runtime_dir)
    task = task_repo.load_task(task_id)
    
    if not task:
        return jsonify({'error': '任务不存在', 'code': 'TASK_NOT_FOUND'}), 404
    
    if task['status'] != 'applied':
        return jsonify({'error': '结果未就绪', 'code': 'RESULT_NOT_READY'}), 400
    
    result = task.get('result')
    if not result or not result.get('error_path'):
        return jsonify({'error': '错误文件不存在', 'code': 'NO_ERROR_FILE'}), 404
    
    # Resolve path - could be relative or absolute
    error_path = Path(result['error_path'])
    if not error_path.is_absolute():
        # Make it absolute relative to project root
        error_path = Path.cwd() / error_path
    
    if not error_path.exists():
        return jsonify({'error': '错误文件不存在', 'code': 'FILE_NOT_FOUND'}), 404
    
    return send_file(error_path, as_attachment=True, download_name=error_path.name)
