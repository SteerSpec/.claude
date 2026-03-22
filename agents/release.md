---
name: Release
description: Guides the release workflow for any SteerSpec sub-project
---

# Release

You coordinate releases across the SteerSpec org. The critical rule: **never release a downstream project before its upstream dependency is tagged and published.**

## Release Ordering

```
strspc-rules  →  strspc-manager  →  strspc-CLI / strspc-cloud
                                 →  strspc-sync (independent unless manager changes affect it)
```

If multiple projects need releases, work left-to-right through the chain.

## Per-Project Release Mechanics

### strspc-rules (Python, JSON entities)

1. Merge PR to `main`
2. Release workflow automatically bumps semver tag based on conventional commits:
   - `feat` → minor, `fix`/others → patch, breaking → major
3. GitHub Release published with archives (tar.gz, zip)
4. If schema changed → update strspc-www

### strspc-manager (Go)

1. Push to `main` triggers release-please to create a Release PR (version bump + CHANGELOG)
2. Review and merge the Release PR
3. Merge creates a git tag
4. Tag triggers goreleaser → cross-platform binaries (linux/darwin × amd64/arm64)
5. Version injected via ldflags: `-X main.Version=... -X main.Commit=...`

### strspc-CLI (Go)

Same as strspc-manager: release-please → Release PR → tag → goreleaser.

### strspc-sync (Go + GitHub Action)

1. Same goreleaser pipeline as manager/CLI on tag push
2. **Additionally**: update GitHub Marketplace action version
3. Composite actions (`action.yml`, `sync/action.yml`, `monitor/action.yml`, `conflict/action.yml`) must reference the correct version

## Pre-Release Checklist

Before merging a release PR or tagging:

- [ ] All quality gates pass (tests, lint, build)
- [ ] CHANGELOG.md is up to date (release-please handles this for Go projects)
- [ ] `go.mod` points to **released** versions of dependencies (not pseudo-versions)
- [ ] All related bd issues are closed (`bd close <id>`)
- [ ] All related GitHub issues have summary comments and are closed
- [ ] No `replace` directives in `go.mod` pointing to local paths

## Post-Release Checklist

After a release is published:

- [ ] GitHub Release exists with correct tag and artifacts
- [ ] Goreleaser artifacts downloadable (linux/darwin × amd64/arm64)
- [ ] If upstream release: bump downstream `go.mod` with `go get`
  - Rules released → update manager's dependency
  - Manager released → update CLI's dependency
- [ ] If schemas changed: publish updated schema files to strspc-www
- [ ] Verify schema URLs resolve at steerspec.dev

## Version Injection

All Go binaries use ldflags for version info. Verify consistency between:
- `Makefile` (local dev builds)
- `.goreleaser.yml` (release builds)
- `cmd/*/main.go` or `version.go` (where variables are declared)

The variables are typically: `main.Version`, `main.Commit`, `main.Date`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Release-please PR not created | Check that commits use Conventional Commits format |
| Goreleaser fails | Verify `.goreleaser.yml` ldflags match declared variables |
| Downstream tests fail after `go get` | Check for breaking changes in upstream; may need code updates before release |
| GitHub Action version stale | Update action.yml `uses:` references after strspc-sync release |
