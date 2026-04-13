#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
WITH_LARK=0
LINK_CODEX=0

for arg in "$@"; do
  case "$arg" in
    --with-lark)
      WITH_LARK=1
      ;;
    --link-codex)
      LINK_CODEX=1
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: bash install.sh [--with-lark] [--link-codex]" >&2
      exit 1
      ;;
  esac
done

echo "==> Checking Python 3"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required but was not found." >&2
  exit 1
fi

echo "==> Creating virtual environment at ${VENV_DIR}"
python3 -m venv "${VENV_DIR}"

echo "==> Installing Python dependencies"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip setuptools wheel
"${VENV_DIR}/bin/python" -m pip install -r "${ROOT_DIR}/requirements.txt"

if [[ "${WITH_LARK}" -eq 1 ]]; then
  echo "==> Installing lark-cli"
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm is required for --with-lark but was not found." >&2
    exit 1
  fi
  npm install -g @larksuite/cli
fi

if [[ "${LINK_CODEX}" -eq 1 ]]; then
  echo "==> Linking skill into Codex"
  mkdir -p "${HOME}/.codex/skills"
  ln -sfn "${ROOT_DIR}/video-teaching-doc-skill" "${HOME}/.codex/skills/video-teaching-doc-skill"
fi

echo
echo "Installation completed."
echo
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source \"${VENV_DIR}/bin/activate\""
echo "2. Read the universal setup guide:"
echo "   ${ROOT_DIR}/UNIVERSAL_SETUP.md"
echo "3. If you need browser-based frame capture, open Chrome and allow:"
echo "   View -> Developer -> Allow JavaScript from Apple Events"
echo
echo "Optional flags:"
echo "  --with-lark   Install lark-cli for Feishu publishing"
echo "  --link-codex  Link the skill into ~/.codex/skills"
