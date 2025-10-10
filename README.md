# GitHub Manager

A small toolset to batch-invite users into GitHub organizations and collect metrics.

## What this project does

- Read normalized CSVs containing Mail / Organization / Team.
- Create missing teams in target organizations (when permitted).
- Invite users into organizations and optionally add them to teams.
- Produce per-invite reports in CSV format under `invitation/reports/`.

## Usage

### Basic Invitation Workflow

1. **Normalize enterprise data**: Use the data transformation pipeline to convert enterprise CSVs into the standard format `Mail,Organization,Team`.

   ```powershell
   venv\Scripts\python -m invitation.pipeline <enterprise_key> <input_csv> [<output_csv>]
   ```

   - `<enterprise_key>`: lower-case key that matches the customize directory and normalizer class (e.g. `sanhua` → `invitation/customize/Sanhua/normalizer.py` → `SanhuaNormalizer`).
   - `<output_csv>` is optional; if omitted, the pipeline writes to `normalized_<input-filename>` alongside the source file.
   - 若目标标准化文件已存在，流水线会保留其中的 `invitation_result` 列并与新的行合并，仅刷新业务字段。

   Example (auto-derived output path):
   ```powershell
   venv\Scripts\python -m invitation.pipeline sanhua invitation\customize\Sanhua\Sanhua_apply.csv
   ```

2. **Run invitations**: Use the normalized CSV to send GitHub invitations。

   > 每次执行成功/失败后，工具会在原始标准化 CSV 中维护一列 `invitation_result`（`success` 或 `failed`），便于后续过滤或复用。

   ```powershell
   venv\Scripts\python -m invitation.inviter <normalized.csv> --organization <OrgName> --token <GITHUB_TOKEN> [--enterprise <key>] [--report <path>]
   ```

### Command Options

**Invitation CLI (`invitation.inviter`)**:
- `--mode` : `grouped` or `individual` (default `grouped`)
- `--report` : path to write results (default `invitation/reports/<enterprise>_invitation_results.csv`)
- `--enterprise` : overrides the enterprise key used for report naming (otherwise inferred from normalized CSV path such as `.../customize/Sanhua/...`)
- `--parent-team` : optionally provide a parent team name for all teams created during this run；若未指定则直接在组织下创建团队
- `--team-prefix` : 邀请前为每个团队名称增加统一前缀（若团队已带此前缀则不会重复添加）
- `--skip-successful` : 跳过标准化 CSV 中已标记 `invitation_result=success` 的行，避免重复邀请
- 若标准化 CSV 包含 `ParentTeam` 列，则依然可为特定行覆盖父团队；若 CLI 传入 `--parent-team`，则以 CLI 值为准。
- `--dry-run` : print planned invitations without calling GitHub API
- `--per-invite-delay` : seconds to wait between invites to reduce burstiness (default 0.5)

**Data Pipeline CLI (`invitation.pipeline`)**:
- First argument: enterprise normalizer key (lower-case, e.g., `sanhua`)
- Second argument: input CSV path
- Optional third argument: output CSV path (default `normalized_<input-filename>` in same directory)

### Handling Rate Limit Failures

If you encounter GitHub's invitation rate limits (50 invites per 24h), use the retry script:

```powershell
venv\Scripts\python -m invitation.bin.retry_failed invitation\reports\invitation_results.csv
```

This will split failed invitations into manageable batches that respect GitHub's limits.

## Enterprise Data Organization

### Public vs Private Files

- **Public** (`invitation/normalizers/`): Contains generic normalizer infrastructure only. No enterprise-specific code or data.
- **Private** (`invitation/customize/<Enterprise>/`): Contains actual enterprise data, mappings, and implementations. **Completely excluded from git via `.gitignore`**.

### Adding New Enterprise Support

1. Create directory `invitation/customize/<Enterprise>/`
2. Add your enterprise-specific normalizer implementation in `normalizer.py`
3. Add your enterprise data files (CSV, documentation, etc.)
4. The public normalizer system will automatically discover and load your implementation

Example structure:
```
invitation/customize/Acme/
   ├── normalizer.py              # AcmeNormalizer implementation
   ├── Acme_apply.csv             # Original enterprise data
   ├── Acme_apply_normalized.csv  # Processed output
   └── Acme.md                    # Enterprise-specific documentation
```

**Important**: No sample files are needed since the entire customize directory is private and excluded from version control.

### Enterprise Isolation Policy (Critical)

To prevent accidental leakage of sensitive enterprise identifiers or user data:

1. Never place real user emails or internal department names outside `invitation/customize/`.
2. Do not add new shim modules (e.g. `acme.py`) under `invitation/normalizers/`.
3. Enterprise-specific logic must live in: `invitation/customize/<Enterprise>/normalizer.py`.
4. Raw source CSVs must NOT be committed; only store them locally under the customize path.
5. Public code MUST remain generic – no company names, email domains, or internal taxonomy.
6. Run the scan script before committing:

```powershell
python scripts/scan_enterprise.py
```

CI：仓库已配置 GitHub Actions（`.github/workflows/ci-enterprise-scan.yml`）在 push / PR 时自动执行上述扫描，确保企业数据不会被误提交。

### Optional Git Pre-Commit Hook

Create `.git/hooks/pre-commit` (and make it executable on non-Windows systems):

```sh
#!/bin/sh
python scripts/scan_enterprise.py || exit 1
```

### Dynamic Loading Recap

| Enterprise Key | Directory | File | Class |
| -------------- | --------- | ---- | ----- |
| `acme`         | `Acme`    | `normalizer.py` | `AcmeNormalizer` |

No hard-coded conditionals are allowed in public modules. The loader derives the path from the key.

See `ENTERPRISE_INTEGRATION.md` for full guidelines.

## Important limitations and notes

- **GitHub Rate Limits**: Organizations commonly have a cap on invitations in a rolling 24h window (e.g., 50 invites/24h). When reached, the API returns 422 `Over invitation rate limit`.
- **Rate vs Volume**: Slowing per-request rate (delay between invites) can reduce endpoint rate-limits but does NOT bypass organization-level daily caps.
- **Security**: Do NOT commit enterprise-specific CSVs, emails, or sensitive mappings. Use `invitation/customize/` and verify `.gitignore` coverage.

## Diagnostics

- Per-invite results are written to `invitation/reports/invitation_results.csv` with `Timestamp` and `Message` fields.
- For 422 responses we log truncated messages in CSV and full JSON in debug logs.
- Use retry tools for batch processing rate-limited failures.

## Contributing

- Add normalizers under `invitation/normalizers/` for public infrastructure
- Add enterprise-specific implementations under `invitation/customize/<Enterprise>/`
- Write tests under `tests/` and run with `pytest`
- Follow the enterprise data security guidelines

