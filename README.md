# SIHOA
SImple HOme Automation

## Configuration

The settings (database, log file, MQTT broker and credentials) live in a `.env` file in the repository root. It is
not versioned, so start from the example:

```bash
cp .env.example .env
```

Every setting can also be given as a command line flag (`python3 -m src.apps.main.sihoa --help`), which wins over
`.env`. To run by hand with the `.env` settings:

```bash
set -a; . ./.env; set +a
python3 -m src.apps.main.sihoa
```

## Running as a service

On the Raspberry Pi, install the systemd service once (it is enabled to start on boot). The service reads `.env`
(if it is missing, the script creates it from `.env.example` and asks you to review it):

```bash
sudo deploy/install-service.sh
```

Then manage it like any other service. After editing `.env`, a restart is enough:

```bash
sudo systemctl start sihoa      # stop | restart | status
sudo systemctl disable sihoa    # do not start on boot (enable to undo)
journalctl -u sihoa             # service events; the application log goes to SIHOA_LOG_FILE
```
