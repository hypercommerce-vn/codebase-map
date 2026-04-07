# POST-CM-S3 Hotfix Sprint Plan

**Created:** 2026-04-07
**Trigger:** CEO post-delivery decision after FullTest report
**Target:** v2.0.1 hotfix release
**Total:** ~3 SP · 4 items · 1 day sprint

---

## Backlog (from FullTest_PreDelivery_2026-04-07.md §8)

| # | ID | Item | SP | Owner | Priority |
|---|----|------|----|-------|----------|
| 1 | POST-CM-S3-01 | Hook real coverage data into Executive health bar (replace layer-diversity proxy) | 1 | Tech Lead | 🟡 |
| 2 | POST-CM-S3-02 | Fix CM-AC-05 self-build false positive — exclude tools from "unknown" classification when scanning own repo | 0.5 | Tech Lead | 🟢 |
| 3 | POST-CM-S3-03 | API Catalog placeholder — better empty state copy for Python-only projects | 0.5 | Designer + TL | 🟢 |
| 4 | POST-CM-S3-04 | Auto-bake `pr_diff.json` in `generate` when `--diff <ref>` flag passed (eliminate manual 2-step) | 1 | Tech Lead | 🟡 |
| **Total** | | | **3** | | |

---

## Day Plan (1-day hotfix sprint)

| Slot | Task | Owner |
|------|------|-------|
| AM 1 | POST-CM-S3-04 — `generate --diff <ref>` flag | Tech Lead |
| AM 2 | POST-CM-S3-01 — Coverage hook into exec health | Tech Lead |
| PM 1 | POST-CM-S3-02 — Self-build exclusion | Tech Lead |
| PM 2 | POST-CM-S3-03 — API Catalog empty state copy + visual | Designer + TL |
| PM 3 | Local Pre-flight + Mode 2 Remote Full review-gate | PM coordinates |
| EOD | PR + CEO approve + tag v2.0.1 | CEO |

## Acceptance Criteria
- [ ] HOTFIX-AC-01: `codebase-map generate -c x.yaml --diff main` produces HTML with PR Diff baked in single command
- [ ] HOTFIX-AC-02: Executive health bar shows real coverage % when `coverage.xml` present in cache
- [ ] HOTFIX-AC-03: Self-build report shows correct layer distribution (no >90% "unknown" false positive)
- [ ] HOTFIX-AC-04: API Catalog tab shows informative empty state for non-routed projects
- [ ] All CI green
- [ ] Mode 2 Remote Full ≥95/100

## Review Gate
Standard 2-tier (Local Pre-flight → Mode 2 Remote Full). Tester + CTO + Designer per Rule #9.

## Rollout
- Tag: `v2.0.1`
- Release notes: bug fixes section
- Notify customer (if delivered) via release notes link

---

*Plan owner: PM · Contributors: Tech Lead, Designer · Approval: CEO*
