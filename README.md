# GitHub Manager

批量邀请用户加入 GitHub 组织 / 团队 + AI 辅助 CSV 标准化的工具集。

> 版本：v0.2.1（更新日期：2025-10-31） · [查看 Release Notes](docs/RELEASE_NOTES.md)

---
## 目录结构概览
| 目录 | 作用 |
|------|------|
| `invitation/` | 邀请与标准化核心逻辑 |
| `invitation/customize/<Enterprise>/` | 企业私有标准化脚本（不入库）|
| `invitation/reports/` | 邀请执行结果、重试批次 |
| `docs/` | 配置、需求、发布说明等文档 |

---
## 一、快速开始（从 CSV 到成功邀请）
| 步骤 | 说明 | 命令示例 |
|------|------|----------|
| 1 | 创建/激活虚拟环境并安装依赖 | `python -m venv venv` / `venv\Scripts\activate` / `pip install -r requirements.txt` |
| 2 | 准备原始企业 CSV | 放到 `invitation/customize/<Enterprise>/` 下 |
| 3 | 生成标准化文件（AI 或自定义 normalizer） | `venv\Scripts\python -m invitation.ai_normalizer_cli raw.csv` 或使用已有 normalizer/pipeline |
| 4 | 检查标准化输出 `_clean.csv` 是否包含列：`Mail, Team, Organization` | 手动打开或用表格工具预览 |
| 5 | 试运行（不调用 API） | `venv\Scripts\python -m invitation.inviter cleaned.csv --dry-run` |
| 6 | 正式执行邀请 | `venv\Scripts\python -m invitation.inviter cleaned.csv --mode grouped` |
| 7 | 查看结果与报告 | 原 CSV `invitation_result` 列 + `invitation/reports/*.csv` |
| 8 | 若触发配额上限执行重试批次生成 | `venv\Scripts\python -m invitation.bin.retry_failed --input invitation\reports\xxx_results.csv` |

---
## 二、标准化输出要求
| 字段 | 必须 | 说明 |
|------|------|------|
| `Mail` | 是 | 用户邮箱（区分大小写字段名） |
| `Organization` | 是 | GitHub 组织名 |
| `Team` | 是（内容可为空） | 为空表示只加组织不加团队 |
| `ParentTeam` | 否 | 行级父团队（CLI `--parent-team` 可覆盖）|
| `invitation_result` | 否 | 运行后由程序写入/更新（success/failed）|

列顺序推荐（工具当前已保证）：`Mail, Team, Organization, ...其他列`。

---
## 三、AI 辅助标准化（可选）
使用自然语言描述转换：
```cmd
venv\Scripts\python -m invitation.ai_normalizer_cli input.csv
```
交互过程：分析列 → 询问/确认规则 → 生成并展示安全代码 → 执行生成 `_clean.csv` 与 `_report.csv`。

详细配置、供应商矩阵、降级逻辑参见：`docs/CONFIGURATION.md`。

核心环境变量（节选）：
| 变量 | 用途 | 说明 |
|------|------|------|
| `API_TYPE` | openai/github/azure/custom | 供应商类型 |
| `API_KEY` | LLM 密钥 | github 可回退 `GITHUB_TOKEN`（警告）|
| `MODEL_NAME` | 模型 | 默认 `gpt-4o` |
| `API_BASE_URL` | 自定义/azure 端点 | 其他供应商可空 |
| `DEFAULT_ORGANIZATION` | 预留 | 未来可用于邀请缺省值 |
| `DEFAULT_TEAM_PREFIX` | 预留 | 未来可用于前缀补全 |

---
## 四、邀请执行命令详解
基础命令：
```cmd
venv\Scripts\python -m invitation.inviter normalized_or_clean.csv
```
常用参数：
| 参数 | 说明 | 示例 |
|------|------|------|
| `--mode` | `grouped`(默认)：按 (Org,Team,Parent) 分组；`individual`：逐行 | `--mode individual` |
| `--report` | 指定结果 CSV 输出路径 | `--report invitation\reports\sanhua_invitation_results.csv` |
| `--skip-successful` | 跳过已有 `invitation_result=success` 的行 | `--skip-successful` |
| `--organization` | 过滤只处理某些组织，可重复 | `--organization OrgA --organization OrgB` |
| `--team` | 过滤团队，可重复 | `--team Backend --team QA` |
| `--parent-team` | 为所有团队统一设置父团队（优先级高于行内 `ParentTeam`） | `--parent-team China-Dev` |
| `--team-prefix` | 为所有非空团队名前加前缀（已含前缀则跳过） | `--team-prefix SH-` |
| `--dry-run` | 不调用 GitHub API，仅打印计划 | `--dry-run` |
| `--per-invite-delay` | 每个邀请之间 sleep 秒数 | `--per-invite-delay 1.0` |
| `--token` | 指定 GitHub Token（优先于环境变量） | `--token ghp_xxx` |
| `--enterprise` | 指定企业 key 影响报告文件命名 | `--enterprise sanhua` |

执行后：
1. 生成/更新报告：`invitation/reports/<enterprise>_invitation_results.csv`
2. 回写输入 CSV：添加/更新 `invitation_result` 列（success/failed）
3. 日志中列出 SUCCESS / FAILURE 统计

---
## 五、团队创建与父子层级规则
1. 先按输入收集所有 (Organization, Team, ParentTeam) 组合
2. 列出组织现有团队（`GET /orgs/{org}/teams`）
3. 不存在 → 若指定父团队：
   - 父团队不存在则尝试创建父团队
   - 再创建子团队（带 `parent_team_slug`）
4. 未指定父团队则直接创建团队
5. `--team-prefix` 在创建前完成修改并写回 CSV 行

---
## 六、速率限制与重试
GitHub 组织邀请通常存在 24 小时配额（例如 50）。出现 422 / Over invitation rate limit：
1. 首次执行完成后查看报告
2. 生成分批重试文件：
   ```cmd
   venv\Scripts\python -m invitation.bin.retry_failed --input invitation\reports\<enterprise>_invitation_results.csv
   ```
3. 按生成的 `invitation/reports/retry_batches/<Org>/batch_n.csv` 在下一窗口重新执行 inviter。

脚本策略：按时间排序 → 滑动 24 小时窗口 → 每批最多 50 条。

---
## 七、典型场景命令速查
| 场景 | 命令 |
|------|------|
| 首次全量邀请 | `invitation.inviter xxx_clean.csv --mode grouped` |
| 只重跑失败且跳过成功 | `invitation.inviter xxx_clean.csv --skip-successful` |
| 仅邀请指定组织 | `invitation.inviter file.csv --organization MyOrg` |
| 仅邀请指定多个团队 | `invitation.inviter file.csv --team Backend --team QA` |
| 批量给团队加前缀 | `invitation.inviter file.csv --team-prefix SH-` |
| 强制所有团队挂到一个父团队 | `invitation.inviter file.csv --parent-team HQ` |
| 验证计划不真正执行 | `invitation.inviter file.csv --dry-run` |
| 逐条执行（调试） | `invitation.inviter file.csv --mode individual` |
| 处理 retry 批次 | `invitation.inviter invitation\reports\retry_batches\Org\batch_1.csv` |

> Windows 下如已激活 venv，`python -m invitation.inviter` 与 `venv\Scripts\python -m invitation.inviter` 等价；未激活时需写全路径确保使用虚拟环境解释器。

---
## 八、Token / 环境变量与 .env 说明
邀请逻辑（`invitation.inviter`）本身 **不会自动读取 `.env` 文件**。若你希望通过 `.env` 提供 `GITHUB_TOKEN`：
1. 安装 `python-dotenv`（若未安装）
2. 在执行前手动 `set GITHUB_TOKEN=...`，或
3. 写一个小的启动脚本自行 `from dotenv import load_dotenv; load_dotenv()` 然后调用 `main()`。

推荐做法（Windows CMD）：
```cmd
set GITHUB_TOKEN=ghp_xxx
venv\Scripts\python -m invitation.inviter xxx_clean.csv
```
或直接用参数：
```cmd
venv\Scripts\python -m invitation.inviter xxx_clean.csv --token ghp_xxx
```

差异说明：
| 方式 | 是否需激活 venv | 依赖可用性 | 说明 |
|------|-----------------|-----------|------|
| `venv\Scripts\python -m ...` | 不需要（显式指定解释器） | 始终使用 venv | 最稳妥 |
| 激活后 `python -m ...` | 需要先 `venv\Scripts\activate` | 使用已激活 venv | 常规方式 |
| 系统全局 `python -m ...` | 否 | 可能缺依赖 | 不推荐 |

---
## 九、诊断与排查
| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 缺少必需列报错 | 列名大小写不匹配 | 确认首字母大写：`Mail` 等 |
| 403 | Token scope 不足 | PAT 需含 `admin:org` |
| 422 Over invitation rate limit | 组织配额耗尽 | 生成 retry 批次等待窗口 |
| 422 Unprocessable invitation | 邮箱无效/重复 pending | 让用户接受或取消旧邀请 |
| 409 Conflict | 已有待处理邀请 | 等待或清理旧记录 |
| 团队未创建 | 权限不足或父团队创建失败 | 检查 token 权限 / 名称冲突 |

---
## 十、企业隔离与安全
见：`ENTERPRISE_INTEGRATION.md` 与扫描脚本：
```cmd
python scripts/scan_enterprise.py
```

不要提交：真实邮箱 / 内部部门结构 / 原始源数据。

---
## 十一、后续改进（Roadmap 摘要）
- 将 `.env` 自动加载加入邀请 CLI（需评估安全）
- DEFAULT_ORGANIZATION / DEFAULT_TEAM_PREFIX 深度整合
- 增加并发 + 排队节流策略
- 增加 web UI (后续版本)

---
## 十二、贡献
1. Fork & Branch
2. 编写或扩展 normalizer / CLI 功能
3. 添加测试：`pytest`
4. 提交 PR，遵循文档与安全规范

---
## License
内部/私有使用（如需开放请补充明确协议）。

---
如需更详细说明，请阅读：
- `docs/CONFIGURATION.md`
- `docs/requirements/req-ai-assisted-normalization.md`
- `docs/RELEASE_NOTES.md`

（本文档已依据最新讨论重写。）

