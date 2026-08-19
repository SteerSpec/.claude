# SteerSpec · Claude Code configuration

Shared **agents**, **skills** and **settings** for working across the
[SteerSpec](https://steerspec.dev) repositories — packaged as an installable Claude Code plugin
marketplace.

If you work in more than one SteerSpec repo, this is the config that travels with you: the same
review conventions, the same release rules, the same understanding of which repo a change belongs
in.

---

## Install

```
/plugin marketplace add SteerSpec/.claude
```

The agents and skills below become available in every repo you open. Nothing else to configure.

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
| **pr-caller-sync** | The `pr-auto-approve` action changed and caller repos need matching updates |

More skills live **in the repos they document**, rather than here, so they version with the code
they describe and cannot drift into describing an unreleased version. See
[`SteerSpec/strspc-pr-review`](https://github.com/SteerSpec/strspc-pr-review) for setup and
diagnostic skills covering the PR auto-approval action.

## settings.json

An org-level permission allowlist, so routine read-only work — `git`, `gh`, GitHub MCP lookups —
doesn't stop to ask. It grants nothing destructive.

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
skills/              # skills scoped to this repo
settings.json        # org-level permission allowlist
```

## Contributing

Every change goes through a pull request — direct pushes to `main` are rejected by an organization
ruleset, and PRs require an approving review.

Agents and skills are plain markdown with YAML frontmatter (`name`, `description`). The
`description` is what decides whether the agent or skill gets picked, so write it as *when to use
this*, not *what this is*.
