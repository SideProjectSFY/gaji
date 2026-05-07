#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="$ROOT/_bmad-output/implementation-artifacts"
if [ ! -d "$TARGET" ]; then
  echo "FAIL: implementation artifacts directory missing: $TARGET"
  exit 1
fi
STORY_DIR="$TARGET/stories"
if [ ! -d "$STORY_DIR" ]; then
  echo "FAIL: story directory missing: $STORY_DIR"
  exit 1
fi

# Require at least one V2 story file in expected key format.
if ! ls -1 "$STORY_DIR" | rg -q '^[1-8]-[0-9]+-.*\.md$'; then
  echo "FAIL: no V2 story files found under $STORY_DIR"
  exit 1
fi

STATUS_FILE="$TARGET/sprint-status.yaml"
if [ ! -f "$STATUS_FILE" ]; then
  echo "FAIL: sprint status file missing: $STATUS_FILE"
  exit 1
fi

# Every story key in sprint status must have a corresponding story file.
MISSING=0
while IFS= read -r key; do
  if [ ! -f "$STORY_DIR/${key}.md" ]; then
    echo "FAIL: missing story file for sprint key: $key"
    MISSING=1
  fi
done < <(rg -o '^\s{2}\d+-\d+-[^:]+' "$STATUS_FILE" | sed 's/^[[:space:]]*//')

if [ "$MISSING" -ne 0 ]; then
  exit 1
fi

echo "PASS: artifact locations and sprint story file mappings are valid"
