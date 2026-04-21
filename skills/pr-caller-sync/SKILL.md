---
name: pr-caller-sync
description: Use when the pr-auto-approve action in SteerSpec/strspc-pr-review changes and caller repos need to be updated. Triggered by: adding/removing event triggers, changing job conditions, updating permissions, or any other structural change that callers must mirror.
---

# PR Auto-Approve Caller Sync

**Goal:** After changing the `pr-auto-approve` action in `strspc-pr-review`, find all caller repos and open PRs with the matching updates.

## The Problem

`strspc-pr-review` hosts the composite action (`action.yml`) and the reusable workflow `.github/workflows/pr-auto-approve.yml` (deprecated).
Caller repos have their own workflow that invokes the action via `uses: SteerSpec/strspc-pr-review@vX.Y.Z`.

When the action gains a **new trigger** or changes its **job `if:` condition**, callers must be updated too — otherwise they never forward the new event to the action.

The caller workflow's job condition is defense-in-depth. Both must be kept in sync.

## 1. Identify what changed

```bash
git diff main -- action.yml
```

Look for changes to:
- Inputs added or removed
- Logic changes that require new event types in the caller `on:` section
- Job condition changes (the caller owns concurrency and `if:` guards)

Also check the caller template for the current recommended pattern:

```bash
cat templates/pr-auto-approve.yml
```

## 2. Find all caller repos

```bash
gh search code "uses: SteerSpec/strspc-pr-review" \
  --json repository,path
```

Each result is a caller. Note the repo name and file path.

## 3. Determine the caller diff

| Action change | Caller must update |
|---|---|
| New event type needed (e.g. `check_run`) | Add to `on:` section |
| New job `if:` condition branch | Add matching `||` branch |
| New `concurrency.group` fallback | Update the group expression |
| New input available | Optionally wire it up |

**Self-exclusion pattern**: callers use `github.event.check_run.name != '<job-name>'` to prevent
feedback loops. The job name in the template is `auto-approve` — if callers rename their job,
they must update this filter to match.

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

SteerSpec/strspc-pr-review#<PR> changed the pr-auto-approve action.
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
|---|---|
| Updating the action but forgetting callers | Always search for `uses: SteerSpec/strspc-pr-review` references before closing the PR |
| Copying the trigger but not the job condition | Both must be updated — the trigger fires the job, the condition gates it |
| Missing the self-exclusion filter | Callers must exclude their own job name from `check_run` events |
| Using a token without `workflow` scope | `gh auth refresh -s workflow` before pushing |
| Merging strspc-pr-review before callers | Callers first (or simultaneous) so no events drop in the window |
