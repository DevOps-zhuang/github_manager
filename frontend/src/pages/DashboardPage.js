import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { normalizeAPI } from '../api/client';
import { getUsername, clearAuth } from '../utils/auth';
import './DashboardPage.css';

function DashboardPage() {
  const [file, setFile] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const [task, setTask] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const username = getUsername();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile);
      setError('');
    } else {
      setError('请选择CSV文件');
      setFile(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await normalizeAPI.createTask(file);
      const { task_id } = response.data;
      setTaskId(task_id);
      await loadTask(task_id);
    } catch (err) {
      setError(err.response?.data?.error || '上传失败');
    } finally {
      setLoading(false);
    }
  };

  const loadTask = async (id) => {
    try {
      const response = await normalizeAPI.getTask(id || taskId);
      setTask(response.data);
    } catch (err) {
      setError('加载任务失败');
    }
  };

  const handleChat = async () => {
    if (!message.trim() || !taskId) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await normalizeAPI.chat(taskId, message);
      setTask(prev => ({
        ...prev,
        ...response.data,
      }));
      setMessage('');
    } catch (err) {
      setError(err.response?.data?.error || '对话失败');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (!taskId) return;
    
    setLoading(true);
    setError('');
    
    try {
      await normalizeAPI.apply(taskId);
      await loadTask(taskId);
      alert('标准化执行成功！');
    } catch (err) {
      setError(err.response?.data?.error || '执行失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!taskId) return;
    
    try {
      const response = await normalizeAPI.download(taskId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'normalized_result.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('下载失败');
    }
  };

  const handleLogout = () => {
    clearAuth();
    navigate('/login');
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>🚀 AI辅助CSV标准化</h1>
        <div className="user-info">
          <span>👤 {username}</span>
          <button onClick={handleLogout} className="logout-btn">退出</button>
        </div>
      </div>

      <div className="dashboard-content">
        {error && <div className="error-message">{error}</div>}

        {!taskId ? (
          <div className="upload-section">
            <h2>上传CSV文件</h2>
            <div className="upload-zone">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                id="file-input"
              />
              <label htmlFor="file-input" className="file-label">
                {file ? `📄 ${file.name}` : '📁 选择CSV文件'}
              </label>
              {file && (
                <button onClick={handleUpload} disabled={loading} className="upload-btn">
                  {loading ? '上传中...' : '开始处理'}
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="task-section">
            <div className="task-info">
              <h3>任务信息</h3>
              <p><strong>任务ID:</strong> {taskId}</p>
              <p><strong>状态:</strong> <span className={`status-${task?.status}`}>{task?.status}</span></p>
              {task?.result?.stats && (
                <div className="stats">
                  <p><strong>总行数:</strong> {task.result.stats.total_rows}</p>
                  <p><strong>成功:</strong> {task.result.stats.success_rows}</p>
                  <p><strong>错误:</strong> {task.result.stats.error_rows}</p>
                </div>
              )}
            </div>

            {task?.status !== 'applied' && (
              <div className="chat-section">
                <h3>💬 规则调整</h3>
                <div className="conversation">
                  {task?.conversation?.slice(-6).map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role}`}>
                      <strong>{msg.role === 'user' ? '👤 您' : '🤖 助手'}:</strong>
                      <p>{msg.content}</p>
                    </div>
                  ))}
                </div>
                <div className="chat-input">
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleChat()}
                    placeholder="描述您需要的转换规则..."
                    disabled={loading}
                  />
                  <button onClick={handleChat} disabled={loading || !message.trim()}>
                    发送
                  </button>
                </div>
              </div>
            )}

            {task?.preview?.rows && task.preview.rows.length > 0 && (
              <div className="preview-section">
                <h3>📊 预览（前{task.preview.rows.length}行）</h3>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        {Object.keys(task.preview.rows[0]).map(col => (
                          <th key={col}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {task.preview.rows.map((row, idx) => (
                        <tr key={idx}>
                          {Object.values(row).map((val, i) => (
                            <td key={i}>{val}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="action-buttons">
              {task?.status !== 'applied' && (
                <button onClick={handleApply} disabled={loading} className="apply-btn">
                  ✅ 确认执行标准化
                </button>
              )}
              {task?.status === 'applied' && (
                <>
                  <button onClick={handleDownload} className="download-btn">
                    📥 下载标准化结果
                  </button>
                  <button onClick={() => { setTaskId(null); setTask(null); setFile(null); }} className="new-task-btn">
                    🆕 处理新文件
                  </button>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default DashboardPage;
