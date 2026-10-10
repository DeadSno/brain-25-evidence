# Worktree patches — 2026-10-10

Archive of uncommitted changes from linked OpenCode worktrees before they were
deleted together with `~/.local/share/opencode/worktree`.

- Repo: `C:\analytics\brain-25-evidence`
- Branch: `v5.6-dev`
- Main worktree HEAD at time of capture: `42c9cb2`
- Patches captured with `git diff --binary HEAD` (after `git add -A -N` so that
  untracked files are included). Each patch applies to its worktree's own base
  commit listed below — none of these worktrees shared the main HEAD.

## Actual dirty set vs. the set named in the task

The task named `curious-cactus`, `eager-cabin`, `shiny-wizard`, `swift-island`,
`tidy-eagle`. A full scan of **all** linked worktrees found only these dirty
(verified twice, `git status --porcelain --untracked-files=all`):

| worktree | base commit | patch | bytes | contents |
|---|---|---|---|---|
| `eager-cabin`   | `3b6b0f2` | eager-cabin.patch   | 37894 | AGENTS.md, docs/version.json, tests/conftest.py, tests/test_server_gate.py |
| `shiny-planet`  | `5df807c` | shiny-planet.patch  | 81704 | _tmp_fb375_before.png, _tmp_hdr_int_375.png (binary) |
| `cosmic-knight` | `31f9b0d` | cosmic-knight.patch | 2846  | docs/style.css |
| `misty-cabin`   | `31f9b0d` | misty-cabin.patch   | 2008  | docs/style.css |
| `swift-island`  | `f86811e` | swift-island.patch  | note  | phantom CRLF only — no content (see file) |

- `curious-cactus`, `shiny-wizard`, `tidy-eagle` were **clean** (no changes) —
  they produced nothing, which is why they are not in the table.
- The valuable item is **`eager-cabin`**: it contains the uncommitted
  server-gate implementation (`tests/conftest.py` + new
  `tests/test_server_gate.py`) plus the AGENTS.md/version.json edits that go
  with it.
- Correction: there is **no `context.py`** anywhere in any worktree. The file
  the task meant is `tests/conftest.py` (the server gate). `eager-cabin` does
  contain an unchanged top-level `conftest.py`.

## Notes

- `eager-cabin`, `misty-cabin` and `swift-island` also showed the two snapshot
  `.gitignore` files as modified; these are phantom CRLF entries and produce no
  diff hunk, so the patches above contain only real content.
- `shiny-planet`'s patch holds two PNGs (≈80 KB) — kept for completeness, but
  they look like throwaway `_tmp_*` screenshots.
