# Patching

## What it does

Security fixes for the operating system reach every container automatically, every
day. Everything else — Proxmox itself and the software that does not come from
Debian — is updated by hand, after a snapshot.

## How it is built

- **Containers:** `unattended-upgrades` with two small files in `/etc/apt/apt.conf.d/`
  ([`configs/patching/`](../configs/patching/)):
  - `20auto-upgrades` turns on the daily package-list refresh and upgrade run;
  - `52security-only` restricts it to the `Debian-Security` origin.

  It never reboots a container and never touches packages from other repositories.
- **Proxmox VE:** the no-subscription repository is enabled and the enterprise
  repository, which needs a paid subscription, is removed. Proxmox posts a low-priority
  notification when updates are available; they are applied by hand.
- **Software from outside Debian,** updated by hand after a snapshot.

## What runs, and how it is updated

Versions as read on the node when these pages were written; Caddy, on CT 112, was read
when it was added. Every service container runs Debian 13.7; the node runs Proxmox VE
9.2.21 on kernel 7.0.14.

| Software | Version | Comes from | Updated |
|---|---|---|---|
| Unbound | 1.26.2 | Debian | Automatically (security) |
| Prometheus | 2.53.3 | Debian | Automatically (security) |
| Syncthing | 1.29.5 | Debian | Automatically (security) |
| PostgreSQL, Redis | 17.11, 8.0.2 | Debian | Automatically (security) |
| Caddy | 2.6.2 | Debian | Automatically (security) |
| Pi-hole | Core 6.5, Web 6.6.1, FTL 6.8 | Its own installer | `pihole -up` |
| Tailscale | 1.104.2 | Tailscale's apt repository | `apt-get install --only-upgrade tailscale` |
| ntfy | 2.34.0 | ntfy's apt repository | `apt-get install --only-upgrade ntfy` |
| Grafana | 13.2.4 | Grafana's apt repository | `apt-get install --only-upgrade grafana` |
| prometheus-pve-exporter | 3.10.1 | PyPI, in a virtualenv | `pip install -U prometheus-pve-exporter` in the venv |
| Uptime Kuma | 2.5.6 | Git release tag | Check out the new release tag and reinstall |
| NetBox | 4.7.3 | Release tarball | The upgrade procedure in NetBox's docs, carrying over `configuration.py` and `gunicorn.py` |
| Homepage | 2.5.0 | Built from source | Build the new release; keep `config/` and the icons |
| Node.js (for Homepage) | 22.23.4 | Official tarball | Swap the tarball behind `/opt/node` |

## Why this way

- **Security only, automatically.** Security updates within a Debian release are small
  and low-risk, and waiting for someone to apply them is the bigger risk.
- **Everything else on purpose.** A new Pi-hole or Grafana version can change
  behavior. It is applied when someone can watch it, with a snapshot to roll back to.

## How to verify

On the node, for each service container:

```sh
pct exec 106 -- systemctl is-enabled apt-daily-upgrade.timer        # enabled
pct exec 106 -- ls /etc/apt/apt.conf.d/52security-only              # present
pct exec 106 -- unattended-upgrade --dry-run -d 2>&1 | grep "Allowed origins"
# only origins with label=Debian-Security
```
