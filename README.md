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
/plugin install strspc-pr-review@steerspec
/plugin install strspc-pr-review-skills@steerspec
```

The first is the four agents, kept here. The second is skills, cross-linked from the repo they
document — see [Skills](#skills) for why they are not in this repo.

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
that repo's release tag ([`v1.4.0`](https://github.com/SteerSpec/strspc-pr-review/releases/tag/v1.4.0)),
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
server. There is no `deny` list. If you copy this file, narrow it to what you actually need.

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
agents/              # the four agents above, one markdown file each
settings.json        # org-level permission allowlist
```

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

You may use, modify and redistribute the agents, skills and settings here, including commercially,
provided you keep the notices in [`NOTICE`](NOTICE). The cross-linked plugin resolves from
`strspc-pr-review`, which is under the same license.
