#!/bin/bash

cd /opt/OpenTTS || exit 1

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Dirty working tree, skipping update"
  exit 0
fi

git fetch origin

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
  echo "Update found, pulling..."

  git pull --rebase

  systemctl restart opentts.service
else
  echo "No update"
fi
