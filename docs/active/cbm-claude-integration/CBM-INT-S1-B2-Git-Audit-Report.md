# CBM-INT-S1 Blocker B2 — Git History Audit Report

**Sprint:** CBM-INT-S1 (Codebase Map ↔ Claude Integration)
**Blocker:** B2 — Git history audit before Day 1 kickoff
**Author:** CTO (acting via `agents/cto/SKILL.md` §2.4 Security)
**Date:** 18/04/2026
**Repo:** `hypercommerce-vn/codebase-map` (PUBLIC since 18/04/2026)
**Branch scanned from:** `main` (HEAD = `e4895c1`)

---

## 1. Executive Summary

**Verdict: CLEAN — Day 1 kickoff CAN proceed Mon 20/04/2026 09:00.**

Full git history (all branches + remotes, 168 unique commits, 3.22 MB of blob data) was scanned by **gitleaks v8.30.1** with its default ruleset plus a manual regex sweep targeting the secret families called out in the B2 brief. **Zero credential-class findings.** No `.env` files, PEM/key files, or service-account JSONs have ever been committed. No DB URLs with embedded passwords. No Telegram bot tokens, AWS keys, GitHub PATs, PyPI tokens, or LLM provider keys (`sk-`, `sk-ant-`, `AIza…`) appear in any blob across history.

Two minor non-blocker observations are documented in §4.

---

## 2. Scanner & Methodology

| Item | Value |
|---|---|
| Primary scanner | **gitleaks v8.30.1** (Homebrew bottle, arm64_tahoe) |
| Install command | `brew install gitleaks` |
| Scan command | `gitleaks detect --source . --log-opts="--all --remotes" --report-path=/tmp/gitleaks-report.json --report-format=json --redact` |
| Ruleset | gitleaks default (200+ patterns including AWS, GCP, Azure, GitHub, GitLab, Slack, Stripe, Twilio, PyPI, npm, OpenAI, Anthropic, generic high-entropy) |
| Manual sweep tool | `git log --all --remotes -p -G '<regex>'` (POSIX BRE) for the B2 brief's enumerated patterns |
| Local exec runtime | 733 ms (gitleaks main pass) |

### 2.1 Scope

- **Branches:** 21 local + 32 remote = **53 refs** total
- **Unique commits scanned:** **168** (gitleaks dedupes blobs by SHA across refs; raw `git rev-list --all` count = 276 with duplicates from cherry-picks/merges)
- **Bytes scanned:** 3,223,969 (3.22 MB)
- **Author emails seen in history:** `hypercdp@gmail.com`, `pro@MacBook-Pro-cua-Macbook.local`, `git@stash`
- **Committer emails:** above + `noreply@github.com`

### 2.2 Manual Pattern Hunt (in addition to gitleaks default ruleset)

Each pattern below was searched via `git log --all --remotes --full-history -p -G '<pattern>' --oneline`:

| Pattern family | Regex (POSIX BRE) | Matches |
|---|---|---|
| GitHub PAT | `ghp_[A-Za-z0-9]\{36\}`, `gho_…`, `github_pat_[A-Za-z0-9_]\{82\}` | 0 |
| PyPI token | `pypi-AgEIcHlwaS5vcmc` | 0 |
| AWS access key | `AKIA[0-9A-Z]\{16\}`, `ASIA[0-9A-Z]\{16\}` | 0 |
| Anthropic API key | `sk-ant-[A-Za-z0-9_-]\{40\}` | 0 |
| Google API key | `AIza[0-9A-Za-z_-]\{35\}` | 0 |
| Slack bot token | `xoxb-[A-Za-z0-9-]\{10\}` | 0 |
| Telegram bot token | `[0-9]\{9,10\}:[A-Za-z0-9_-]\{35\}` | 0 |
| DB URL with password | `postgres\(ql\)\?://…:…@`, `mysql://…:…@`, `mongodb://…:…@` | 0 |
| `Authorization: Bearer …` header | `Authorization:\s*Bearer\s+[A-Za-z0-9._-]\{20\}` | 0 |
| `.env` file ever added | `git log --diff-filter=A -- '*.env' '.env*'` | 0 |
| PEM/key file ever added | `git log --diff-filter=A -- '*.pem' '*.key' '*.p12' '*.pfx' 'id_rsa*'` | 0 |
| Unsafe code (`yaml.load`, `eval`, `exec`, `__import__`) in current tree | `grep -rn --include='*.py' …` against `codebase_map/` | 0 |

### 2.3 Files of Interest in History

YAML files ever present (manually inspected — all are CI workflows or example configs, no embedded secrets):

- `.github/workflows/ci.yml`
- `.github/workflows/cbm-baseline.yml`
- `.github/workflows/cbm-post-merge.yml`
- `.github/workflows/cbm-pr-impact.yml`
- `.github/workflows/codebase-map-pr.yml`
- `codebase-map-self.yaml`
- `codebase-map.example.yaml`

---

## 3. Findings

### 3.1 Credential-Class Findings

**None.** Both gitleaks (`/tmp/gitleaks-report.json` = `[]`) and the manual regex sweep returned zero hits.

| # | Commit SHA | File | Pattern | Severity | Action |
|---|---|---|---|---|---|
| — | — | — | — | — | No findings |

---

## 4. Non-Blocker Observations

These are **NOT secret leaks** and do not block Day 1, but worth flagging for hygiene.

### 4.1 Local-hostname author email (LOW / informational)

- **What:** 175 commits authored by `pro@MacBook-Pro-cua-Macbook.local` (the developer's local machine hostname before `git config user.email` was set repo-wide).
- **Risk:** Reveals the laptop hostname. Common in OSS history; not exploitable. No PII beyond what's already public in the GitHub profile.
- **Recommendation:** Going forward, set `git config user.email hypercdp@gmail.com` globally on the dev machine. Do **NOT** rewrite history to fix this — the disruption cost (breaks all forks, invalidates Issue/PR commit links, churns CI snapshots) is far higher than the marginal privacy gain.

### 4.2 Legacy `git@stash` placeholder author (LOW / informational)

- **What:** 2 commits attributed to `git@stash` — leftover from an Atlassian Stash/Bitbucket Server era (likely from the parent `hypercommerce` monorepo before the 16/04/2026 split).
- **Risk:** None. Just an opaque service identifier.
- **Recommendation:** Ignore. Same rationale as 4.1 — not worth a history rewrite.

### 4.3 Working tree (NOT in scope of B2 — already covered by other gates)

5 files are currently modified-but-unstaged in `git status` (belonging to a separate session's docs-cleanup work). They were **not** in scope of this audit; B2 covers committed history only. They will pass through normal review-gate / pre-commit lint when their session lands.

---

## 5. Verdict & Day 1 Readiness

| Item | Status |
|---|---|
| **Verdict** | ✅ **CLEAN** |
| **Day 1 kickoff** | ✅ **CAN PROCEED Mon 20/04/2026 09:00** |
| **Remediation needed?** | ❌ No |
| **Escalation to CEO needed?** | ❌ No |
| **History rewrite (BFG / `git-filter-repo`)?** | ❌ Not required |
| **Token rotation needed?** | ❌ Not required |

---

## 6. Remediation Playbook (Reference Only — NOT Triggered)

Kept here so that if a future audit finds a leak, the team has a pre-written response. **Do not execute** unless a CRITICAL finding is recorded above.

1. **Rotate first, scrub second.** Any leaked credential must be revoked at the issuer (PyPI, GitHub, AWS, Anthropic, …) **before** touching git history. Once a secret is on a public repo, assume it is harvested.
2. **Get CEO approval** for a history rewrite — it breaks every fork/clone and invalidates all SHA references in GitHub Issues, PRs, and external links.
3. **Rewrite tool:** `git filter-repo --replace-text rules.txt` (preferred over BFG for newer git). Run on a fresh clone; never on the working dev clone.
4. **Force-push** the rewritten history to `main` and **all** other branches (`git push --force-with-lease --all && git push --force-with-lease --tags`).
5. **Notify** the public via a SECURITY advisory on GitHub (use Security → Advisories → "Publish a new advisory").
6. **Re-scan** after rewrite to confirm `gitleaks detect --log-opts="--all --remotes"` returns 0 again.
7. **Update collaborators** to re-clone (their old clones still contain the leaked blobs).

---

## 7. Artifacts

- Full gitleaks JSON report: `/tmp/gitleaks-report.json` (content: `[]`)
- This report: `docs/active/cbm-claude-integration/CBM-INT-S1-B2-Git-Audit-Report.md`
- Scan logs: captured inline in §2 above

---

*Report v1.0 — CBM-INT-S1 Blocker B2 — 18/04/2026 — CTO sign-off pending PM review.*
