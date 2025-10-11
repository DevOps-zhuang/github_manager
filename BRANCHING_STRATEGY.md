# Git 分支管理最佳实践

## 分支角色一览

| 分支 | 用途 | 更新方式 |
| --- | --- | --- |
| `main` | 生产环境（Prod）。只接受经过验证的发布版本，保持可随时部署。 | **仅能通过 Pull Request 合并**，禁止直接推送。 |
| `release` | 测试 / 预发布环境（Test）。用于候选版本的验证、回归测试与发布演练。 | 从 `develop` 挑选稳定代码创建或快进，**仅能通过 Pull Request** 更新。 |
| `develop` | 开发集成环境（Dev）。整合最新完成的特性，作为团队联调分支。 | Feature 分支通过 Pull Request 合并。 |
| `feature/<name>` | 单一功能、缺陷修复或 Spike 的短期分支。 | 从 `develop` 派生，功能完成后通过 Pull Request 回到 `develop`。 |
| `hotfix/<name>` | 线上紧急修复。 | 从 `main` 派生，修复后分别合并回 `main` 与 `develop`。 |

> 说明：若团队需要长期维护多个大版本，可额外设置 `maintenance/<version>` 类分支。本文默认项目采用单主线。

## 日常开发流程

1. **同步主线**：
   ```powershell
   git checkout develop
   git pull origin develop --ff-only
   ```
2. **创建功能分支**：
   ```powershell
   git checkout -b feature/<short-summary>
   ```
3. **开发与提交**：
   - 按功能或问题拆分提交，使用约定式提交信息（如 `feat:`, `fix:`）。
   - 保持分支专注，避免跨需求改动。
4. **本地验证**：
   - 运行单元测试、静态检查、`python scripts/scan_enterprise.py` 等质量门禁。
   - 必要时更新文档或示例数据。
5. **推送并创建 Pull Request**：
   ```powershell
   git push -u origin feature/<short-summary>
   ```
   - PR 目标分支为 `develop`。
   - 填写变更说明、测试结果及影响面。
6. **代码评审**：
   - 至少一名 Reviewer 审核通过。
   - CI 必须全部通过，尤其是企业泄漏扫描与测试任务。
7. **合并策略**：
   - 推荐 `squash-merge` 或 `merge commit`（根据团队约定）。
   - 删除本地与远程 Feature 分支，保持仓库整洁。

## 发布与环境分支

1. **准备发布**：
   - 当 `develop` 达到发布标准时，创建或快进 `release`：
     ```powershell
     git checkout release
     git merge --ff-only develop
     ```
   - 在 `release` 分支上执行回归测试、性能验证与文档审校。
2. **修复回滚**：
   - 针对测试中发现的问题，在 `release` 分支修复后，通过 Pull Request 同步回 `develop`，确保主干一致。
3. **上线**：
   - 测试通过后，将 `release` 快进或合并到 `main`：
     ```powershell
     git checkout main
     git merge --ff-only release
     git tag v<version>
     git push origin main --tags
     ```
   - 发布成功后，可选择将 `release` 再次与 `develop` 同步，保持分支一致性。

## 紧急热修流程

1. 从 `main` 创建 `hotfix/<issue>` 分支。
2. 修复完成后：
   ```powershell
   git checkout main
   git merge --ff-only hotfix/<issue>
   git tag v<version+1>
   git push origin main --tags

   git checkout develop
   git merge --ff-only hotfix/<issue>
   git push origin develop
   ```
3. 删除 `hotfix` 分支。

## Pull Request 审核清单

- ✅ 说明清晰：背景、变更点、测试结果。
- ✅ 代码通过自动化检查（CI、企业扫描、单元测试）。
- ✅ 无敏感信息泄漏（确认 `invitation/customize` 未被提交）。
- ✅ 关联任务/Issue 已标注。

## 分支保护与权限建议

- 为 `main`、`release`、`develop` 设置保护规则：
  - 禁止直接推送，强制 Pull Request。
  - 强制通过 CI 检查（构建、测试、扫描）。
  - 要求至少一名 Reviewer。
- 限制标签权限，仅限发布负责人操作。
- 对 Feature/Hotfix 分支放宽限制，但仍鼓励定期同步和及时删除。

## 定期维护与清理

- 每周检查未合并的 Feature 分支并制定下一步计划。
- 利用 Git hooks 或 CI 自动运行 `python scripts/scan_enterprise.py`，避免企业数据泄漏。
- 发布后整理文档与变更记录，保持 `README.md`、`BRANCHING_STRATEGY.md` 等资料最新。

## 推荐工具与自动化

- **CI/CD**：GitHub Actions 或 Azure Pipelines。
- **质量门禁**：`pytest`、`ruff`/`flake8`、`mypy`（可在 `requirements-dev.txt` 中管理）。
- **发布自动化**：使用脚本生成发行说明，自动创建 Git 标签与发布包。

> 按照以上策略，可以确保代码在开发、测试、生产环境间有清晰的迁移路径，同时通过 Pull Request 审核与自动化检查，保证质量与安全。