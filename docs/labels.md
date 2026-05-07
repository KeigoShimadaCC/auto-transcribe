# Issue & PR label taxonomy

This repo uses a small, mutually exclusive label set so triage is fast and
release-please can group entries cleanly.

| Label | Meaning |
|---|---|
| `type:bug` | A defect: behaviour deviates from documented intent. |
| `type:feat` | New user-visible capability. |
| `type:chore` | Maintenance: dependency bumps, tooling, refactors with no user-visible change. |
| `type:docs` | Documentation-only change. |
| `priority:high` | Blocks a release or affects a core happy-path user flow. |
| `priority:low` | Nice-to-have; can sit in the backlog without harm. |
| `area:engine` | Anything under `src/auto_transcribe/engines/` or pipeline decode/transcribe path. |
| `area:ui` | Tk UI (`ui_tk.py`) and `.command` launchers. |
| `area:ci` | GitHub Actions workflows, pre-commit hooks, lint/test config. |
| `area:deps` | `pyproject.toml`, lockfile, Dependabot PRs. |
| `area:docs` | README / AGENTS / QUICKSTART / `docs/`. |

## Conventions

- Every issue gets exactly one `type:*`, exactly one `area:*`, and at most one `priority:*`.
- `type:*` is mirrored in the Conventional Commit prefix on the resolving PR
  (`type:bug` -> `fix:`, `type:feat` -> `feat:`, `type:chore` -> `chore:` /
  `build:` / `ci:` / `refactor:` / `test:`, `type:docs` -> `docs:`). This keeps
  release-please CHANGELOG sections in sync with the issue tracker.
- Dependabot PRs are auto-labelled `type:chore` + `area:deps` (or `area:ci`
  for `github-actions` ecosystem) by `.github/dependabot.yml`.

## Creating the labels

Run once with the GitHub CLI:

```bash
gh label create "type:bug"      --color "d73a4a" --description "A defect"           --force
gh label create "type:feat"     --color "0e8a16" --description "New capability"     --force
gh label create "type:chore"    --color "cfd3d7" --description "Maintenance"        --force
gh label create "type:docs"     --color "0075ca" --description "Documentation"      --force
gh label create "priority:high" --color "b60205" --description "Release blocker"    --force
gh label create "priority:low"  --color "fef2c0" --description "Nice to have"       --force
gh label create "area:engine"   --color "5319e7" --description "Engines / pipeline" --force
gh label create "area:ui"       --color "1d76db" --description "Tk UI / launchers"  --force
gh label create "area:ci"       --color "c5def5" --description "CI / tooling"       --force
gh label create "area:deps"     --color "ededed" --description "Dependencies"       --force
gh label create "area:docs"     --color "bfdadc" --description "Docs"               --force
```
