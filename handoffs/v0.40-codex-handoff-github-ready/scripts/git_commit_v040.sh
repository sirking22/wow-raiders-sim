#!/usr/bin/env bash
set -euo pipefail
BRANCH="v040-codex-handoff-hex-field-standard"
git checkout -b "$BRANCH" || git checkout "$BRANCH"
python scripts/verify_v040.py
git add .
git commit -m "feat: add v0.40 Codex handoff and hex field standard"
echo "Ready: git push -u origin $BRANCH"
