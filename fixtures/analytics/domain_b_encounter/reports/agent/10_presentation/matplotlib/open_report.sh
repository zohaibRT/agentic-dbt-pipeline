#!/usr/bin/env bash
# Enterprise-safe launcher: blocked until REPORT_HANDOFF_READINESS open_allowed=true
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
HANDOFF_CHECK=""
if [[ -f "${PROJECT_ROOT}/scripts/check_report_handoff_readiness.py" ]]; then
  HANDOFF_CHECK="${PROJECT_ROOT}/scripts/check_report_handoff_readiness.py"
elif [[ -f "${SCRIPT_DIR}/../../../../../scripts/check_report_handoff_readiness.py" ]]; then
  HANDOFF_CHECK="$(cd "${SCRIPT_DIR}/../../../../../scripts" && pwd)/check_report_handoff_readiness.py"
fi

if [[ -z "${HANDOFF_CHECK}" ]]; then
  echo "Report artifacts were generated, but the report is not ready to open."
  echo "Runtime and browser verification are still pending."
  echo "Missing check_report_handoff_readiness.py"
  exit 1
fi

if ! python "${HANDOFF_CHECK}" --root "${PROJECT_ROOT}" --phase final --require-pass; then
  echo ""
  echo "Report artifacts were generated, but the report is not ready to open."
  echo "Runtime and browser verification are still pending."
  echo "See reports/agent/10_presentation/REPORT_HANDOFF_READINESS.json"
  exit 1
fi

PORT="${REPORT_PORT:-8765}"
python "${SCRIPT_DIR}/serve_report.py" --host 127.0.0.1 --port "${PORT}" &
SERVER_PID=$!
trap 'kill "${SERVER_PID}" 2>/dev/null || true' EXIT
sleep 2
URL="http://127.0.0.1:${PORT}/"
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${URL}" >/dev/null 2>&1 || true
elif command -v open >/dev/null 2>&1; then
  open "${URL}" >/dev/null 2>&1 || true
fi
echo "Verified report handoff: serving ${URL} (pid ${SERVER_PID})"
wait "${SERVER_PID}"
