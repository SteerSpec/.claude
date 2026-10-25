# SteerSpec · Claude Code configuration

Shared **agents**, **skills** and **settings** for working across the
[SteerSpec](https://steerspec.dev) repositories. This repo doubles as a Claude Code plugin
marketplace, so one command installs the lot.

If you work in more than one SteerSpec repo, this is the config that travels with you: the same
review conventions, the same release rules, the same understanding of which repo a change belongs
in.

---

## Install

```
/plugin marketplace add SteerSpec/.claude
```

That registers the marketplace. Install the two plugins it publishes:

```
/plugin install strspc-agents@steerspec
/plugin install strspc-pr-review-skills@steerspec
```

`strspc-agents` is the four agents, kept here. `strspc-pr-review-skills` is the skills for the
[pr-auto-approve](https://github.com/SteerSpec/strspc-pr-review) action, cross-linked from the repo
they document — see [Skills](#skills) for why they are not in this repo.

---

## Agents

Specialists you can delegate to. Each one carries the org context you'd otherwise have to explain
every time.

| Agent | Use it when |
|---|---|
| **Architect** | *"Where does this change go?"* — navigates the tiered architecture and checks dependency direction before you write code in the wrong layer |
| **Agile PM** | Decomposing a goal into sequenced work across repos, respecting the dependency chain, tracked in [beads](https://github.com/gastownhall/beads) |
| **Code Review** | Reviewing a change against SteerSpec conventions, with checklists that vary by which tier it touches |
| **Release** | Coordinating a release — enforces the rule that upstream is tagged and published before anything downstream |

## Skills

Task-specific playbooks that trigger automatically when the work matches.

| Skill | Use it when |
|---|---|
| **pr-auto-approve-setup** | Wiring the PR auto-approval action into a repo for the first time |
| **pr-auto-approve-diagnose** | A PR wasn't auto-approved and you need to know which guard stopped it |
| **pr-caller-sync** | The `pr-auto-approve` action changed and caller repos need matching updates |

These live **in the repo they document**, not here. This marketplace cross-links them, pinned to
that repo's release tag ([`v1.7.1`](https://github.com/SteerSpec/strspc-pr-review/releases/tag/v1.7.1)),
so a skill can never describe behaviour that isn't released yet.

That is not a hypothetical. This repo used to keep its own copy of `pr-caller-sync`; by the time it
was removed it still told you to give caller workflows a `pull_request` trigger — the one that lets
any PR read the bot token, fixed upstream in v1.4.0. A copy has no way to know the thing it
describes has moved on.

## settings.json

An org-level permission allowlist (57 entries), so routine work — `git`, `gh`, GitHub MCP lookups —
doesn't stop to ask on every call.

**Read it before adopting it.** It is tuned for trusted maintainers working in this org, not
hardened for general use. Among other things it allows `Bash(git:*)` (which includes `push --force`
and `reset --hard`), `Bash(gh repo:*)` (which includes `gh repo delete`), `pip install` and `go get`
(both execute code fetched from the network), and issue/repository writes through the GitHub MCP
server. A short `deny` list blocks the usual spellings of force pushes, hard resets,
`gh repo delete` and `rm -rf` regardless of the allows; it is a backstop, not a sandbox. If
you copy this file, narrow it to what you actually need.

## Org-wide sync

This repo is also the central configuration for
[strspc-sync](https://github.com/SteerSpec/strspc-sync), applied to SteerSpec itself.
`steerspec-sync.yml` lists the managed templates and the target repos; today that is the
`org-standards` block of every repo's `CLAUDE.md`, rendered from
`templates/CLAUDE.md.mustache` with the marker strategy, so each repo keeps its own notes
around the managed section.

Three workflows drive it, all authenticated as the **steerspec-sync** GitHub App (org
secrets `STEERSPEC_APP_ID` and `STEERSPEC_PRIVATE_KEY`):

| Workflow | When | What |
|---|---|---|
| `steerspec-sync.yml` | push to `main` touching the templates or config, or by hand | Opens or updates one PR per repo and template; records the result in `.steerspec/deployment-state.json` |
| `steerspec-monitor.yml` | weekly | Opens a `steerspec-drift` issue in a repo whose managed files no longer match, closes it when they do again |
| `steerspec-conflict.yml` | weekly | Flags local Claude Code configuration that contradicts the org-managed one |

The App's PRs run CI and auto-approve in the target repos like any other PR; merging stays
a human decision there. To rehearse a template change without writing anything, dispatch
`steerspec-sync.yml` with the `dry-run` input on (or set `sync.dry-run: true` in the config).

---

## How SteerSpec fits together

Context the agents rely on, in short:

```
strspc-rules    (Python)  canonical rule definitions
      ↓
strspc-manager  (Go)      the enforcement engine
      ↓
strspc-CLI      (Go)      user-facing CLI          strspc-cloud  (planned)
```

**Dependencies point strictly downward.** The manager never imports the CLI, and the CLI never
reimplements rule logic — it delegates.

Alongside those: **strspc-sync** distributes `.claude/` configs across the org via PRs,
**strspc-pr-review** publishes the [PR auto-approve action](https://github.com/marketplace/actions/pr-auto-approve-copilot),
and **strspc-www** serves [steerspec.dev](https://steerspec.dev).

Ask the **Architect** agent for the full decision tree.

---

## Layout

```
.claude-plugin/
  marketplace.json   # plugin manifest — what /plugin marketplace add reads
agents/              # the four agents above (plugin strspc-agents), one markdown file each
settings.json        # org-level permission allowlist and deny list
steerspec-sync.yml   # strspc-sync central config: managed templates and target repos
templates/           # the templates it distributes (CLAUDE.md org-standards block)
.steerspec/          # deployment-state.json, written by the sync workflow
docs/ORG_SETUP.md    # how to reuse this repo in another organization
```

## Reusing this in your org

See [docs/ORG_SETUP.md](docs/ORG_SETUP.md): which files to copy unchanged, which to rewrite,
and the bot, ruleset and secret prerequisites the workflows assume.

## Contributing

Every change goes through a pull request — direct pushes to `main` are rejected by an organization
ruleset, and PRs require an approving review.

Agents are plain markdown with YAML frontmatter (`name`, `description`). The `description` is what
decides whether the agent gets picked, so write it as *when to use this*, not *what this is*. CI
checks that frontmatter is present and that a skill's directory name matches its `name`.

New skills belong in the repo whose behaviour they describe, cross-linked here at that repo's
release tag — not copied into this one.

`.claude-plugin/marketplace.json` carries a `version` per plugin, and CI bumps the patch on every
PR. That is deliberate: Claude Code caches an installed plugin under its version string, so an
unchanged version means clients keep serving the old copy and never see new skills.

## License

[Apache License 2.0](LICENSE) — the SteerSpec standard, shared with
[`strspc-pr-review`](https://github.com/SteerSpec/strspc-pr-review),
[`strspc-manager`](https://github.com/SteerSpec/strspc-manager) and
[`strspc-rules`](https://github.com/SteerSpec/strspc-rules).

You may use, modify and redistribute the agents, skills and settings here, including commercially.
Redistribution comes with conditions — among them supplying a copy of the license, marking files you
changed, retaining existing notices, and passing on [`NOTICE`](NOTICE). Section 4 of the
[LICENSE](LICENSE) is the authority; treat this sentence as a pointer to it, not a summary of it.

The cross-linked `strspc-pr-review-skills` plugin resolves from
[`strspc-pr-review`](https://github.com/SteerSpec/strspc-pr-review), which is under the same license.
