#!/bin/sh
set -eu

# Cloud Run provides PORT dynamically; the committed Valhalla config is local-dev port 8002.
config_path="/tmp/valhalla-cloud-run.json"
sed "s#tcp://\*:8002#tcp://\*:${PORT:-8080}#" /custom_files/valhalla.json > "$config_path"

exec valhalla_service "$config_path" 1
