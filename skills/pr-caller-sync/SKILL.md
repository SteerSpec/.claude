---
name: pr-caller-sync
description: Use when the pr-auto-approve reusable workflow in SteerSpec/strspc-pr-review changes and caller repos need to be updated. Triggered by: adding/removing event triggers, changing job conditions, updating permissions, or any other structural change that callers must mirror.
---

# PR Auto-Approve Caller Sync

**Goal:** After changing the `pr-auto-approve` reusable workflow in `strspc-pr-review`, find all caller repos and open PRs with the matching updates.

## The Problem

`strspc-pr-review` hosts the reusable workflow `.github/workflows/pr-auto-approve.yml`.
Caller repos have their own thin wrapper that invokes it via `uses:`.

When the reusable workflow gains a **new trigger** or changes its **job `if:` condition**, callers must be updated too — otherwise they never forward the new event to the reusable workflow.

The reusable workflow's job condition is defense-in-depth (it duplicates the caller's guard). Both must be kept in sync.

## 1. Identify what changed

```bash
git diff main -- .github/workflows/pr-auto-approve.yml
```

Look for changes to:
- `on:` trigger section (new event types added or removed)
- Job `if:` condition (new branches allowing additional event types)
- `concurrency.group` (new context fields used as fallback keys)
- `permissions:` (new scopes required)

## 2. Find all caller repos

```bash
gh search code "uses: SteerSpec/strspc-pr-review/.github/workflows/pr-auto-approve.yml" \
  --json repository,path
```

Each result is a caller. Note the repo name and file path.

## 3. Determine the caller diff

For each trigger or condition change in the reusable workflow, the caller needs:

| Reusable workflow change | Caller must add |
|--------------------------|-----------------|
| New `on:` event (e.g. `check_run`) | Same event under `on:` |
| Wider job `if:` condition | Same `\|\|` branch in its own `if:` |
| New `concurrency.group` fallback | Same expression update |
| New `permissions:` scope | Same scope in caller `permissions:` |

**Self-exclusion pattern**: if the reusable workflow excludes its own job name to prevent feedback loops (e.g. `github.event.check_run.name != 'Auto-approve if Copilot conditions met'`), copy the exact same exclusion into the caller condition.

## 4. Open PRs in each caller repo

Updating `.github/workflows/` files requires a token with **`workflow` scope**.

```bash
# Check / add workflow scope
gh auth status
gh auth refresh -s workflow

# Push change to caller repo
gh api --method PUT \
  repos/<owner>/<caller-repo>/contents/.github/workflows/pr-auto-approve.yml \
  -f message="fix(ci): sync pr-auto-approve caller with strspc-pr-review" \
  -f content="$(base64 -i /path/to/updated-file.yml)" \
  -f sha="$(gh api repos/<owner>/<caller-repo>/contents/.github/workflows/pr-auto-approve.yml --jq .sha)" \
  -f branch="fix/sync-pr-auto-approve-caller"

gh pr create --repo <owner>/<caller-repo> \
  --base main \
  --title "fix(ci): sync pr-auto-approve caller with strspc-pr-review changes" \
  --body "Mirrors SteerSpec/strspc-pr-review#<PR>. See that PR for rationale."
```

## 5. PR body template

```markdown
## Why

SteerSpec/strspc-pr-review#<PR> changed the reusable pr-auto-approve workflow.
This caller must mirror those changes so the new event types are forwarded correctly.

## What changed

- Added `<event>: [completed]` to `on:` so the workflow fires on CI completion
- Updated job `if:` to allow `<event>` events (with self-exclusion to prevent loops)

## Test plan
- [ ] Merge strspc-pr-review PR first
- [ ] Verify workflow triggers on the new event in a test PR
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Updating reusable workflow but forgetting callers | Always search for `uses:` references before closing the strspc-pr-review PR |
| Copying the trigger but not the job condition | Both must be updated — the trigger fires the job, the condition gates it |
| Missing the self-exclusion filter | Copy it verbatim from the reusable workflow `if:` |
| Using a token without `workflow` scope | `gh auth refresh -s workflow` before pushing |
| Merging strspc-pr-review before callers | Callers first (or simultaneous) so no events drop in the window |
