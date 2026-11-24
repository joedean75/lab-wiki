# GitHub repositories

All under one account. The pipeline and Forge repos are **private**; this wiki's source is public.

| Local folder | Branch | Holds |
|---|---|---|
| `Books\Pipeline_assistant` | `main` | Assistant pipeline + core. `data/`, `runs/`, `out/`, `*.zip` ignored. |
| `Books\Pipeline_coder` | `main` | Coder pipeline + core. |
| WSL `~/cad` | `v18-prep` (work), `training-v9-v17` (history) | Forge. `main` untouched. |
| `Books\Pipeline_copilot` | — | Trainer, server, launch scripts; allow-list `.gitignore` (scripts + last datasets + a winner adapter). |
| `Books\Pipeline_astra` | — | Astra. |
| `Books\Pipeline_claude` | `main` | Pipeline_claude. `runs/`, `*.pth` ignored. |


## How to use it

```bash
git status                       # always look first
git add <files>                  # name files; avoid adding data or runs
git commit -m "..."              # one card or change per commit
git push
gh repo view <private-repo>     # gh CLI: C:\Program Files\GitHub CLI\gh.exe
```

Rules: commit and push only when the owner asks; never commit anything from
`Pipeline_assistant\data\exports\`; check `.gitignore` covers large outputs before `git add`.
