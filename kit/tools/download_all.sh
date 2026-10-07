#!/bin/bash
# Download every line that isn't on disk yet; retry until all are present (max ~12 min).
# Runs in the project folder (wvf tool download_all); the project's tools/flow_download.py overrides the package's.
cd "${WVF_PROJECT_ROOT:-$PWD}"
FLOW_DOWNLOAD="tools/flow_download.py"
[ -f "$FLOW_DOWNLOAD" ] || FLOW_DOWNLOAD="$(dirname "$0")/flow_download.py"
for round in $(seq 1 12); do
  missing=0
  for id in L01 L02 L03 L04 L05 L06 L07 L08 L09 L10; do
    if [ -f "flow/$id.mp4" ] || ls flow/$id/*.mp4 >/dev/null 2>&1; then continue; fi
    missing=1
    echo "== round $round $id"
    "${WVF_PYTHON:-python3}" "$FLOW_DOWNLOAD" $id 2>&1 | tail -2
  done
  [ $missing -eq 0 ] && echo ALL_DONE && exit 0
  sleep 45
done
echo GAVE_UP
