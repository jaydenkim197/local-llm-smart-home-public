#!/usr/bin/env bash

set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"
PROJECT_LOG_DIR="$HOME/Library/Logs/LocalLLMSmartHome"
PROJECT_LOG_FILE="$PROJECT_LOG_DIR/git-autosync.log"

mkdir -p "$PROJECT_LOG_DIR"

log() {
  local message="$1"
  printf '%s [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "mac" "$message" | tee -a "$PROJECT_LOG_FILE"
}

fail() {
  log "ERROR: $1. Local work was preserved."
  exit 1
}

pause() {
  log "PAUSED: $1. Inspect git status and resolve deliberately."
  exit 2
}

git_at_root() {
  git -C "$REPOSITORY_ROOT" "$@"
}

if ! git_at_root rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  fail "Not a Git working tree: $REPOSITORY_ROOT"
fi

GIT_DIR="$(git_at_root rev-parse --git-dir)"
case "$GIT_DIR" in
  /*) ;;
  *) GIT_DIR="$REPOSITORY_ROOT/$GIT_DIR" ;;
esac

for marker in MERGE_HEAD REBASE_HEAD CHERRY_PICK_HEAD index.lock; do
  if [ -e "$GIT_DIR/$marker" ]; then
    pause "Git operation marker found: $marker"
  fi
done

for marker_dir in rebase-merge rebase-apply; do
  if [ -d "$GIT_DIR/$marker_dir" ]; then
    pause "Git operation directory found: $marker_dir"
  fi
done

log "Fetching origin/main."
git_at_root fetch origin --prune || fail "Fetch failed"

if ! git_at_root diff --quiet || ! git_at_root diff --cached --quiet || [ -n "$(git_at_root ls-files --others --exclude-standard)" ]; then
  git_at_root add -A || fail "Could not stage local changes"
  if ! git_at_root diff --cached --quiet; then
    git_at_root commit -m "autosync(mac): $(date '+%Y-%m-%d %H:%M %Z')" || fail "Snapshot commit failed"
    log "Created a local snapshot commit."
  fi
fi

if git_at_root merge-base --is-ancestor origin/main HEAD; then
  :
else
  log "Rebasing local commits onto origin/main."
  if ! git_at_root rebase origin/main; then
    pause "Rebase stopped with a conflict"
  fi
fi

if git_at_root merge-base --is-ancestor HEAD origin/main; then
  log "Sync complete; main already matches origin/main."
  exit 0
fi

log "Pushing main to origin."
git_at_root push origin main || fail "Push failed"
log "Sync complete."
