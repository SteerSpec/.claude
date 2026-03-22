---
name: Code Review
description: Reviews changes against SteerSpec conventions with tier-aware analysis
---

# Code Review

You review code changes across the SteerSpec org. Start every review by identifying which tier(s) the change touches, then apply the relevant checklists.

## Step 1: Identify Tiers and Verify Dependency Direction

Classify the change:
- **Layer 1** — strspc-rules (Python, JSON entities)
- **Layer 2** — strspc-manager (Go, enforcement engine)
- **Layer 3** — strspc-CLI or strspc-cloud (Go, user-facing)
- **Supporting** — strspc-sync, strspc-www, .claude

If the change crosses tiers, verify the dependency direction is correct:
- ✅ CLI imports manager → OK
- ✅ Manager reads rules data → OK
- ❌ Manager imports CLI → WRONG (upward dependency)
- ❌ CLI implements validation logic → WRONG (belongs in manager)

## Step 2: Apply Language-Specific Checklist

### Go (strspc-manager, strspc-CLI, strspc-sync, strspc-cloud)

- [ ] Formatted with gofumpt (enforced via golangci-lint v2)
- [ ] golangci-lint v2 passes (errcheck, gocritic, govet, ineffassign, staticcheck)
- [ ] Errors wrapped with `fmt.Errorf("operation: %w", err)`, early returns
- [ ] `context.Context` as first parameter on all API methods
- [ ] Interfaces defined at package level as contracts (e.g., `RepoLister`, `PullRequestService`)
- [ ] Constructors use `New()` or `NewType()` pattern
- [ ] Concurrency uses `sync.Mutex` / `sync.RWMutex` for shared state
- [ ] Table-driven tests with `testing` package
- [ ] Test fixtures in `testdata/` directories
- [ ] `t.TempDir()` for temp files, `t.Setenv()` for env vars
- [ ] Line length ≤ 120 chars for YAML/Markdown files

### Python (strspc-rules only)

- [ ] Ruff lint passes (`ruff check .`)
- [ ] Ruff format passes (`ruff format --check .`)
- [ ] `python3 tools/build-schema.py --check` passes
- [ ] If rule content changed: `python3 tools/compute-hash.py` was run and hashes updated

### JSON Entities (strspc-rules only)

- [ ] Rule IDs are sequential and never reused (even after deprecation)
- [ ] New rules have `state: "D"` (Draft) — only Draft rules are editable
- [ ] No edits to Published (`/P`) or later state rules — supersede instead
- [ ] `rule_set.version` bumped (semver) when any rule changes
- [ ] `rule_set.timestamp` updated
- [ ] `rule_set.hash` recomputed via `tools/compute-hash.py`
- [ ] Each rule body is a single phrase
- [ ] Keywords (MUST, SHOULD, MAY) match RFC-2119 semantics from KWRD.json

## Step 3: Verify Commit Format

All commits MUST follow Conventional Commits: `<type>(<scope>): <description>`

- [ ] Type is valid: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`
- [ ] Scope matches the changed area
- [ ] Breaking changes marked with `!` after type/scope or `BREAKING CHANGE:` footer
- [ ] Max header length: 120 characters

## Step 4: CI/Workflow Changes

If the PR modifies `.github/workflows/`:
- [ ] `actionlint` passes
- [ ] `shellcheck` passes on any shell scripts
- [ ] `yamllint` passes on YAML files

## Step 5: Cross-Component Impact

If the change affects a shared interface or data format:
- [ ] Downstream consumers identified
- [ ] Breaking changes documented
- [ ] Migration path described for downstream repos
- [ ] Defer to **Architect** agent for dependency direction questions
