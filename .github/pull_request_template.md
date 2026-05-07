<!--
Thanks for contributing! Please follow Conventional Commits in the PR title:
  <type>(<scope>)?: <subject>
where <type> is one of: feat, fix, perf, deps, revert, docs, refactor, test,
build, ci, chore. Example: `feat(engine): add Whisper turbo adapter`.
-->

## Summary

<!-- One or two sentences describing the user-visible change. -->

## Why

<!-- The motivation: bug being fixed, capability being added, debt being paid. -->

## Changes

<!-- Bullet list of notable code/config changes. -->

-
-

## Testing

<!-- How you verified this. Paste the relevant `pytest` output or screenshots. -->

```
$ pytest
```

## Screenshots / recordings (UI changes only)

<!-- Drop before/after images or a short clip if Tk UI was touched. -->

## Checklist

- [ ] Conventional Commit subject (`<type>(<scope>)?: <subject>`)
- [ ] `pytest` passes locally (`-n auto`, coverage >= 80%)
- [ ] `ruff check src tests`, `ruff format --check src tests`, `mypy`, `vulture` all clean
- [ ] `README.md` / `QUICKSTART.md` / `AGENTS.md` updated if behaviour or flags changed
- [ ] No models, transcripts, or `ExampleData/` content committed
