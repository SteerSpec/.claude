# Reusing this repo in another organization

This repo is two things: a **mechanism** (a marketplace manifest plus four workflows that
keep it versioned, validated and auto-approved) and **content** (agents, cross-linked skills,
a settings allowlist). Copy the mechanism as-is; rewrite the content, because every line of it
is about SteerSpec.

## 1. Copy the mechanism

| File | What it does | Copy? |
|---|---|---|
| `.claude-plugin/marketplace.json` | What `/plugin marketplace add <org>/.claude` reads | Copy the shape, rename `name`, `owner`, every plugin |
| `.github/workflows/validate.yml` | Checks the manifest and agent/skill frontmatter; also gives the repo a check run, which auto-approve requires | Copy unchanged |
| `.github/workflows/bump-version.yml` | Bumps the patch version of the locally sourced plugin on every PR, through the GraphQL commit API so the commit is signed | Copy unchanged |
| `.github/workflows/release.yml` | Tags and releases each version that lands on `main` | Copy unchanged |
| `.github/workflows/auto-approve.yml` | Approves a PR as the bot once Copilot's review is clean | Copy, then change `bot-login` (two places, see the comment in the file) |
| `.gitignore` | Keeps `settings.local.json` out of the repo | Copy unchanged |
| `.github/workflows/steerspec-sync.yml`, `steerspec-monitor.yml`, `steerspec-conflict.yml` | Run strspc-sync with this repo as the central config (optional, see checklist item 6) | Copy unchanged if you use strspc-sync; they read only org secrets |
| `steerspec-sync.yml`, `templates/` | What strspc-sync distributes and to whom | Rewrite: targets, exclusions and the template text are all SteerSpec's |

Read the header comment of each workflow before changing anything in it. Each one records a
choice that looked optional and was not (`pull_request_target` versus `pull_request`, PAT
versus `GITHUB_TOKEN`, GraphQL commit versus `git push`).

## 2. Rewrite the content

- `agents/*.md`: the four agents encode SteerSpec's tiered architecture, release order and
  review checklists. Keep the frontmatter contract (`name`, `description` written as *when to
  use this*) and replace the bodies.
- Cross-linked skills: the `strspc-pr-review-skills` entry pins another repo's `skills/`
  directory at a release tag. Keep the pattern (skills live in the repo whose behaviour they
  describe) and point it at your own repos, or drop the entry.
- `settings.json`: an allowlist tuned for trusted maintainers plus a `deny` list for the
  commands no agent should run unattended. Start from the deny list and add only the allows
  you need; `Bash(git:*)` is broad on purpose here and may not be right for you. The deny
  patterns are prefix and glob matches on the command text, so they catch the usual
  spellings (`git push --force`, `git push origin main --force`, `git reset HEAD --hard`)
  but not every argument order; treat them as a backstop, not a sandbox.

## 3. Per-org checklist

Everything the workflows assume about the organization, in the order to set it up.

1. **Bot account and PAT.** A machine user (here `cnslr-bt`) with write access to this repo
   and a fine-grained PAT stored as the `BOT_TOKEN` repository secret. Both `auto-approve.yml`
   and `bump-version.yml` need it: a review by the bot satisfies the required-approval rule,
   and a PAT-authored commit re-triggers CI where `GITHUB_TOKEN` would not.
2. **Copilot code review on PRs.** Enable automatic Copilot review for the repo (or org
   ruleset). Auto-approve only acts on a PR Copilot has reviewed and found clean, or after the
   configured number of review rounds.
3. **Branch protection on `main`.** Require a PR, one approving review, conversation
   resolution, signed commits and the `validate` check. The bot's approval counts as the
   review; signed commits are why the bump goes through the GraphQL API.
4. **PR-gating CI.** `validate.yml` is the only required check here. If you add another PR
   workflow, add it to the `workflow_run` list in `auto-approve.yml` so the re-entry fires
   after the last check completes.
5. **Bot-authored PRs need a human.** Auto-approve refuses to approve a PR the bot opened
   itself (the pin-sync PRs from a skills repo, for example). Someone with review rights has
   to approve those by hand.
6. **strspc-sync (optional).** If this repo is also the central config for
   [strspc-sync](https://github.com/SteerSpec/strspc-sync), install the sync GitHub App on
   the org (contents, pull requests and issues write) and store `STEERSPEC_APP_ID` and
   `STEERSPEC_PRIVATE_KEY` as org secrets; the three `steerspec-*.yml` workflows read
   nothing else. The sync writes `.steerspec/deployment-state.json` back to this repo's
   default branch; when an org ruleset forces every change through a PR, add the App as a
   bypass actor for that ruleset or the state write fails. Land `steerspec-sync.yml` with
   `sync.dry-run: true` first and read the job summary before flipping it.
7. **Pin sync from a skills repo (optional).** If another repo publishes skills cross-linked
   here, its pin-sync workflow has to target your marketplace. SteerSpec's
   `strspc-pr-review` hard-codes `TARGET_REPO: SteerSpec/.claude` in
   `sync-marketplace-pin.yml` up to v1.7.1; change that value in your copy. From the release
   that includes SteerSpec/strspc-pr-review#85 it reads the `MARKETPLACE_REPO` repository
   variable instead, with the SteerSpec repo as the default.

## 4. Install

Once `main` has a release:

```
/plugin marketplace add <org>/.claude
/plugin install <plugin-name>@<marketplace-name>
```

`marketplace-name` is the `name` field at the top of `marketplace.json`.
