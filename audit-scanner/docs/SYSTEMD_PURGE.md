# Systemd timer for purging expired encrypted raw files

This file contains example `systemd` unit files to run the `purge_expired.py` helper on a schedule (recommended for self-hosted runners or on-prem storage nodes).

1) Create `/etc/systemd/system/deep-audit-purge.service`:

```
[Unit]
Description=Deep-Audit purge expired encrypted raw files
After=network.target

[Service]
Type=oneshot
User=deep-audit
Group=deep-audit
WorkingDirectory=/opt/deep-audit
ExecStart=/opt/deep-audit/.venv/bin/python /opt/deep-audit/audit-scanner/storage/purge_expired.py /data/deep-audit/raw
```

2) Create `/etc/systemd/system/deep-audit-purge.timer`:

```
[Unit]
Description=Run Deep-Audit purge daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start the timer:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now deep-audit-purge.timer
sudo systemctl status deep-audit-purge.timer
```

Notes:
- Replace paths and user with your deployment-specific locations.
- Ensure the `.venv` has `cryptography` installed and the environment variable `RAW_STORAGE_KEY` is set for the service user.
