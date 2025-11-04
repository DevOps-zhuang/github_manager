# Windows curl 使用指南

由于Windows命令行对引号的处理方式不同，使用curl时需要特别注意。

## 方法1：PowerShell（推荐）

在PowerShell中使用 `Invoke-RestMethod`：

```powershell
# 登录
$body = '{"username":"admin","password":"admin123"}'
$response = Invoke-RestMethod -Method Post -Uri "http://localhost:5000/api/auth/login" -ContentType "application/json" -Body $body
$token = $response.token
Write-Host "Token: $token"

# 使用token上传文件
$headers = @{
    Authorization = "Bearer $token"
}
Invoke-RestMethod -Method Post -Uri "http://localhost:5000/api/normalize/tasks" -Headers $headers -Form @{file=Get-Item "test.csv"}
```

## 方法2：PowerShell使用curl

```powershell
# 登录
$body = '{"username":"admin","password":"admin123"}'
curl.exe -X POST http://localhost:5000/api/auth/login -H "Content-Type: application/json" -d $body

# 注意：使用curl.exe而不是curl（避免PowerShell的curl别名）
```

## 方法3：CMD（命令提示符）

在CMD中，必须转义双引号：

```cmd
curl -X POST http://localhost:5000/api/auth/login -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"admin123\"}"
```

**重要**：在CMD中，JSON字符串内的双引号必须用反斜杠转义（`\"`）

## 方法4：使用文件

创建一个JSON文件（例如 `login.json`）：

```json
{
  "username": "admin",
  "password": "admin123"
}
```

然后使用：

```powershell
# PowerShell
curl.exe -X POST http://localhost:5000/api/auth/login -H "Content-Type: application/json" -d "@login.json"

# CMD
curl -X POST http://localhost:5000/api/auth/login -H "Content-Type: application/json" -d "@login.json"
```

## 方法5：使用Postman或Insomnia

如果curl太复杂，推荐使用GUI工具：
- [Postman](https://www.postman.com/)
- [Insomnia](https://insomnia.rest/)

## 常见错误

### 错误1：EMPTY_BODY

```json
{
  "code": "EMPTY_BODY",
  "error": "请求体不能为空或格式不正确"
}
```

**原因**：JSON格式不正确或引号转义问题

**解决**：
1. 使用PowerShell的 `Invoke-RestMethod`（推荐）
2. 在CMD中正确转义双引号
3. 使用JSON文件

### 错误2：JSON解析失败

**原因**：单引号被错误地包含在请求中

**解决**：确保使用正确的引号转义方式

## 完整工作流示例（PowerShell）

```powershell
# 1. 登录
$body = '{"username":"admin","password":"admin123"}'
$loginResp = Invoke-RestMethod -Method Post `
    -Uri "http://localhost:5000/api/auth/login" `
    -ContentType "application/json" `
    -Body $body

$token = $loginResp.token
Write-Host "登录成功！Token: $($token.Substring(0,20))..."

# 2. 上传CSV文件
$headers = @{
    Authorization = "Bearer $token"
}
$uploadResp = Invoke-RestMethod -Method Post `
    -Uri "http://localhost:5000/api/normalize/tasks" `
    -Headers $headers `
    -Form @{file=Get-Item "test.csv"}

$taskId = $uploadResp.task_id
Write-Host "任务创建成功！Task ID: $taskId"

# 3. 对话修改规则
$chatBody = '{"message":"将Email列转为小写"}'
$chatResp = Invoke-RestMethod -Method Post `
    -Uri "http://localhost:5000/api/normalize/tasks/$taskId/chat" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $chatBody

Write-Host "规则更新成功！"

# 4. 执行标准化
$applyResp = Invoke-RestMethod -Method Post `
    -Uri "http://localhost:5000/api/normalize/tasks/$taskId/apply" `
    -Headers $headers

Write-Host "标准化完成！成功: $($applyResp.stats.success_rows) 行"

# 5. 下载结果
Invoke-RestMethod -Method Get `
    -Uri "http://localhost:5000/api/normalize/tasks/$taskId/download" `
    -Headers $headers `
    -OutFile "result.csv"

Write-Host "结果已下载到 result.csv"
```

## Linux/Mac用户

Linux和Mac用户可以直接使用标准的curl命令：

```bash
# 登录
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

单引号在Unix系统中可以正常工作。
