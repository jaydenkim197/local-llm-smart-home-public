# Cross-Platform Git Workflow

## Purpose

This repository is the source of truth for sequential work between the Mac and Windows workspaces. It is not a live filesystem mirror.

- Remote: `https://github.com/{GITHUB_USER}/local-llm-smart-home.git`
- Shared branch: `main`

```text
Mac workspace -- push --> GitHub repository (main) <-- push -- Windows workspace
      ^                            |                               ^
      +--------- fetch/rebase -----+--------- fetch/rebase ----------+
```

## One-Time Setup

1. Create the GitHub repository and publish the Mac baseline.
2. Clone that repository into a normal local Windows development folder.
3. Confirm that `git fetch` and `git push` work manually on both computers.
4. Do not store either workspace in OneDrive, iCloud Drive, Dropbox, or another live-sync directory.

## Completion Sync

Run the local helper after each meaningful task, before beginning related work on the other computer.

Mac:

```bash
./tools/git-autosync-mac.sh
```

Windows PowerShell:

```powershell
.\tools\git-autosync.ps1
```

The helper follows this order:

1. Refuse to run during a merge, rebase, cherry-pick, or index lock.
2. Fetch `origin`.
3. Snapshot any local work in a timestamped commit.
4. Rebase local commits onto `origin/main` when behind.
5. Push `main` when ahead.

It never force-pushes, discards files, or resolves conflicts automatically.

## Handoff Rule

- Finish one coherent task, including directly affected tests and documentation.
- Run the helper and confirm it exits with `0`.
- On the other computer, run its helper before changing shared files.
- If it exits with `2`, stop work on the other computer and resolve the Git operation deliberately.

## Logs

- Mac: `~/Library/Logs/LocalLLMSmartHome/git-autosync.log`
- Windows: `%LOCALAPPDATA%\LocalLLMSmartHome\git-autosync.log`
