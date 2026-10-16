#!/usr/bin/env bash
# Install (or reinstall) SIHOA as a systemd service and enable it on boot.
#
# Usage, on the Raspberry Pi:
#   sudo deploy/install-service.sh
#
# The settings (database, log file, MQTT broker) are read from <repo>/.env. If it does not exist yet it is created
# from .env.example and the script stops so you can review it. Changing .env later only needs
# "sudo systemctl restart sihoa", not a reinstall.
#
# The repository is the one containing this script and the service runs as the user who called sudo. Python is
# <repo>/.venv/bin/python if it exists, otherwise python3 from the PATH.
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
    echo "Run it with sudo: sudo $0" >&2
    exit 1
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_USER="${SUDO_USER:-root}"
ENV_FILE="${REPO_DIR}/.env"
UNIT_FILE=/etc/systemd/system/sihoa.service

if [[ ! -f "${ENV_FILE}" ]]; then
    install -m 600 -o "${SERVICE_USER}" "${REPO_DIR}/.env.example" "${ENV_FILE}"
    echo "Created ${ENV_FILE} from .env.example. Review it and run this script again."
    exit 1
fi
# The file may hold the MQTT password
chown "${SERVICE_USER}" "${ENV_FILE}"
chmod 600 "${ENV_FILE}"

if [[ -x "${REPO_DIR}/.venv/bin/python" ]]; then
    PYTHON="${REPO_DIR}/.venv/bin/python"
else
    PYTHON="$(command -v python3)"
fi

# Create the log directory, so the service user can write the log file
SIHOA_LOG_FILE="$(sed -n 's/^SIHOA_LOG_FILE=//p' "${ENV_FILE}" | tail -n 1)"
if [[ -n "${SIHOA_LOG_FILE}" ]]; then
    [[ "${SIHOA_LOG_FILE}" = /* ]] || SIHOA_LOG_FILE="${REPO_DIR}/${SIHOA_LOG_FILE}"
    install -d -o "${SERVICE_USER}" "$(dirname "${SIHOA_LOG_FILE}")"
fi

sed -e "s|@USER@|${SERVICE_USER}|g" \
    -e "s|@REPO_DIR@|${REPO_DIR}|g" \
    -e "s|@PYTHON@|${PYTHON}|g" \
    "${REPO_DIR}/deploy/sihoa.service" > "${UNIT_FILE}"

systemctl daemon-reload
systemctl enable sihoa.service

echo "Installed ${UNIT_FILE} (user ${SERVICE_USER}, python ${PYTHON}, settings ${ENV_FILE})"
echo "Start it with: sudo systemctl start sihoa"
