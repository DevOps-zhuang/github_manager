# Enterprise Integration Guide

This document explains how to add enterprise-specific normalization logic **without leaking** any
proprietary identifiers or user data into the public codebase.

## Goals

| Goal | Description |
|------|-------------|
| Isolation | All enterprise logic & data live only under `invitation/customize/<Enterprise>/` |
| Safety | Private directory is excluded via `.gitignore` |
| Generic Core | Public modules (`invitation/normalizers/`) remain company‑agnostic |
| Predictable Loading | Dynamic loader maps an enterprise key to a directory + class convention |

## Directory Convention

```
invitation/
  normalizers/            # Public, generic
    base.py
    mapping.py
    registry.py
  customize/              # Private (ignored by git)
    Acme/
      normalizer.py       # class AcmeNormalizer
      original.csv        # raw source (DO NOT COMMIT)
      normalized.csv      # output (still private)
      README.md           # optional enterprise doc
```

## Dynamic Loader Rules

| Enterprise Key (CLI) | Folder | File | Class |
|----------------------|--------|------|-------|
| `acme`               | `Acme` | `normalizer.py` | `AcmeNormalizer` |

Algorithm (simplified):
1. Take the key provided to the pipeline (e.g. `acme`).
2. Capitalize first letter for folder name (`Acme`).
3. Import: `invitation/customize/Acme/normalizer.py`.
4. Load class `AcmeNormalizer`.
5. Register it into the normalizer registry.

If any step fails --> raise `ImportError` with a guidance message.

## Example Normalizer Skeleton

```python
from invitation.normalizers.base import BaseNormalizer, NormalizedInvitee

class AcmeNormalizer(BaseNormalizer):
    def normalize_row(self, row):
        # Map raw columns to standard fields
        mail = row["Email"].strip()
        org = row.get("Division", "").strip() or "Default-Org"
        team = row.get("Squad", "").strip()
        return NormalizedInvitee(mail=mail, organization=org, team=team)
```

## Validation Checklist Before Use

| Check | Why |
|-------|-----|
| No real emails committed | Prevent data leak |
| No company names in public code | Ensures portability |
| `scripts/scan_enterprise.py` passes | Automated guardrail |
| Class name matches convention | Loader success |
| Output CSV columns = `Mail,Organization,Team` | Inviter compatibility |

## Recommended Local Workflow

1. Place raw enterprise CSV inside `invitation/customize/<Enterprise>/`.
2. Implement/adjust `normalizer.py`.
3. Run pipeline:
   ```powershell
   python -m invitation.pipeline <enterprise_key> \ 
       invitation\customize\<Enterprise>\raw.csv \ 
       invitation\customize\<Enterprise>\normalized.csv
   ```
4. Run scan (should ignore customize directory):
   ```powershell
   python scripts/scan_enterprise.py
   ```
5. Execute invitations using normalized file.

## Do / Do Not

| ✅ Do | ❌ Do Not |
|-------|----------|
| Keep enterprise code private | Put enterprise names in public modules |
| Use dynamic loader | Add `if enterprise == 'xxx'` branches |
| Add README inside enterprise folder | Leak real emails in examples |
| Run scan script pre-commit | Assume reviewers will catch leakage |

## Pre-Commit Hook (Optional)

`.git/hooks/pre-commit` example:
```sh
#!/bin/sh
python scripts/scan_enterprise.py || exit 1
```

## Incident Recovery

If sensitive data was accidentally added and committed:
1. `git rm <file>`
2. `git commit --amend` or new commit removing it
3. If pushed: `git filter-repo` or `git filter-branch` to purge history
4. Rotate any exposed credentials
5. Open internal incident ticket (if required)

## Future Extensions (Optional)

- Pluggable entry-point discovery (setuptools entry points or importlib.metadata)
- Encrypted enterprise bundles outside repo with runtime decryption
- Hash validation of enterprise modules

---
Questions or proposing improvements? Add an internal note in your private enterprise folder.
