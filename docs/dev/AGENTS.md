# Agent Instructions (read automatically)

## Project
Open evidence-based supplement guide. 81 items in docs/data.json.
Manifest: польза > деньги · null честнее выдумки · нет партнёрок.

## Active protocol (docs/MASTER_RUNBOOK.md)
- Rules P1-P32 apply in every session
- Branch v2.7.1-dev active; commits atomic per chunk (P24)
- No rewrites of docs/briefs/* or docs/data.json without explicit permission (P5/P11)
- Files written via VS Code or write_file tool only, never via shell redirect (P31)
- Always verify with pytest + e2e_smoke before commit (P22)
- Approve every opencode edit explicitly (P25)

## Encoding (P27)
- UTF-8 no BOM only
- PowerShell Get-Content lies about encoding — trust python decode('utf-8')
- Suspicious «╨╤╩╧» → git restore + rewrite in VS Code

## Style
- Russian UI, English code/commits
- Card hierarchy: science ≥ 1.2× price (computed style)
- No «₽ за эффект» metric (removed in v2.7.1)

## Economy
- One chunk = one clean session (P26)
- Do not run tests on your own; owner runs pytest + e2e after edits (P22)
- No shell redirects (`>`, `Out-File`) for repo files