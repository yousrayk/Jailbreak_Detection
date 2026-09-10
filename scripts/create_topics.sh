#!/usr/bin/env bash
# Explicitly creates the topics this pipeline depends on, instead of relying
# on Pulsar's implicit auto-creation-on-publish. Keeps the topic list (and
# hence the message contracts in ARCHITECTURE.md) visible in one place.
set -euo pipefail

ADMIN_URL="http://pulsar:8080"
TOPICS=(
  "persistent://public/default/messages.raw"
  "persistent://public/default/predictions.result"
  "persistent://public/default/messages.dlq"
)

for topic in "${TOPICS[@]}"; do
  if bin/pulsar-admin --admin-url "$ADMIN_URL" topics list public/default | grep -qx "$topic"; then
    echo "Topic already exists: $topic"
  else
    echo "Creating topic: $topic"
    bin/pulsar-admin --admin-url "$ADMIN_URL" topics create-partitioned-topic "$topic" -p 1
  fi
done

echo "Topic setup complete."
