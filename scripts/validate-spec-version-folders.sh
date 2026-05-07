#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
V1_DIR="$ROOT/docs/specs/v1"
V2_DIR="$ROOT/docs/specs/mvp-v2"

REQUIRED_V1=(
  "prd.md"
  "architecture.md"
  "epics-v1-legacy.md"
)

REQUIRED_V2=(
  "product-brief-gaji-2026-02-25.md"
  "ux-design-specification.md"
  "architecture-ux-aligned.md"
  "epics-ux-aligned.md"
  "prd-ux-architecture-delta-mapping-v2.md"
  "implementation-readiness-audit-2026-02-27.md"
  "implementation-readiness-latest.md"
  "implementation-readiness-report-2026-02-26.md"
)

DEPRECATED_INDEX_FILES=(
  "$ROOT/docs/index.md"
  "$ROOT/docs/spec-version-map.md"
  "$ROOT/docs/specs/v1/README.md"
  "$ROOT/docs/specs/mvp-v2/README.md"
  "$ROOT/docs/4-implementation/index.md"
  "$ROOT/_bmad-output/implementation-artifacts/index.md"
)

if [ ! -d "$V1_DIR" ]; then
  echo "FAIL: missing V1 folder: $V1_DIR"
  exit 1
fi

if [ ! -d "$V2_DIR" ]; then
  echo "FAIL: missing MVP V2 folder: $V2_DIR"
  exit 1
fi

MISSING=0
for file in "${REQUIRED_V1[@]}"; do
  if [ ! -f "$V1_DIR/$file" ]; then
    echo "FAIL: missing V1 required spec file: $V1_DIR/$file"
    MISSING=1
  fi
done

for file in "${REQUIRED_V2[@]}"; do
  if [ ! -f "$V2_DIR/$file" ]; then
    echo "FAIL: missing MVP V2 required spec file: $V2_DIR/$file"
    MISSING=1
  fi
done

if [ "$MISSING" -ne 0 ]; then
  exit 1
fi

for deprecated in "${DEPRECATED_INDEX_FILES[@]}"; do
  if [ -e "$deprecated" ]; then
    echo "FAIL: deprecated index-based routing file still exists: $deprecated"
    exit 1
  fi
done

echo "PASS: version separation is folder-based and required spec files exist"
