#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION=8.14.3
SHA256=bd71102213493060956ec229d946beee57158dbd89d0e62b91bca0fa2c5f3531
TOOLS="$ROOT/build/tools"
ARCHIVE="$TOOLS/gradle-$VERSION-bin.zip"
GRADLE="$TOOLS/gradle-$VERSION/bin/gradle"
mkdir -p "$TOOLS"
if [[ ! -f "$ARCHIVE" ]]; then
  curl --proto '=https' --proto-redir '=https' -fsSL --retry 3 --connect-timeout 30 \
    "https://services.gradle.org/distributions/gradle-$VERSION-bin.zip" -o "$ARCHIVE"
fi
printf '%s  %s\n' "$SHA256" "$ARCHIVE" | shasum -a 256 -c - >/dev/null
if [[ ! -x "$GRADLE" ]]; then unzip -q "$ARCHIVE" -d "$TOOLS"; fi
"$GRADLE" --no-daemon --console=plain --gradle-user-home "$ROOT/build/coverage/gradle-cache" \
  -p "$ROOT" check jacocoTestReport
