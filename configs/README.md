# Configuration files

Copies of the files that run on `pve01`, by area. Each one was read on the node or
compared with it by SHA-256 (apart from a header comment saying where it lives) when
it was set up or last changed, before the values below were replaced. The two Grafana
provisioning files and the three Homepage files are copies taken when each service was
set up and were not compared. The NetBox configuration was compared line by line, with
its three secrets replaced on the node before the comparison.

**Placeholders:** `<lan>.N` is an address on the home LAN with the network prefix left
out (the host number follows the container ID, as in the [README](../README.md#security-and-privacy)),
`<isp-gateway>` is the ISP's device in front of the home router, `<admin-user>` is a
local login name, `<my-login>` is my Tailscale login, `<my-device>` is one of my
devices' Tailscale address, and `<timezone>` is the server's time zone. Apart from NetBox's
`configuration.py`, whose three secrets are replaced by `<...>`, no secret is in these
files: the scripts read them at run time from root-only files on the node.

Comments inside the copies are the ones on the node; a few were written before the
[firewall](../docs/10-firewall.md) and still say "the LAN" where only my devices get in now,
and the first line of `unbound-pi-hole.conf` still calls Unbound a recursive resolver, as
it was set up before it started forwarding to Quad9
([TSH-04](../troubleshooting/04-isp-intercepted-dns.md)). One exception goes the other way:
the "how to run" comment in `kuma-ntfy.js` was rewritten here, so that the token is read
from its file instead of typed; the copy in CT 105 still shows the older instruction.
The dates in the comments are left out.

| Area | File | On the node | What it does |
|---|---|---|---|
| DNS | [`unbound-pi-hole.conf`](dns/unbound-pi-hole.conf) | CT 100 `/etc/unbound/unbound.conf.d/pi-hole.conf` | Unbound for Pi-hole, from the Pi-hole guide (listens on localhost, DNSSEC, rebinding protection) |
| DNS | [`unbound-forward-quad9.conf`](dns/unbound-forward-quad9.conf) | CT 100 `/etc/unbound/unbound.conf.d/forward-quad9.conf` | Forwards every query to Quad9 over TLS; added later, from this same text |
| Remote access | [`lxc-101-tun.conf`](remote-access/lxc-101-tun.conf) | `/etc/pve/lxc/101.conf` (two lines) | Gives the unprivileged container a TUN device |
| Remote access | [`99-tailscale.conf`](remote-access/99-tailscale.conf) | CT 101 `/etc/sysctl.d/` | IPv4 and IPv6 forwarding |
| Remote access | [`tailnet-policy.hujson`](remote-access/tailnet-policy.hujson) | Tailscale admin console, *Access controls* | Only my devices may use the subnet route and the exit node; tests that block a save which would let anyone else in |
| Monitoring | [`kuma-setup.js`](monitoring/kuma-setup.js) | CT 105 `/opt/uptime-kuma/` | Creates the probes and the status page through Uptime Kuma's API; safe to re-run |
| Monitoring | [`60-unprivileged-ping.conf`](monitoring/60-unprivileged-ping.conf) | CT 105 `/etc/sysctl.d/` | Ping without root in an unprivileged container |
| Monitoring | [`rsyslog-10-router.conf`](monitoring/rsyslog-10-router.conf) | CT 105 `/etc/rsyslog.d/10-router.conf` | Receives the router's syslog on UDP 514 |
| Monitoring | [`logrotate-router`](monitoring/logrotate-router) | CT 105 `/etc/logrotate.d/router` | Keeps 26 weeks of router log |
| Monitoring | [`prometheus.yml`](monitoring/prometheus.yml) | CT 107 `/etc/prometheus/` | Scrapes Prometheus itself and Proxmox through the exporter |
| Monitoring | [`prometheus-pve-exporter.service`](monitoring/prometheus-pve-exporter.service) | CT 107 `/etc/systemd/system/` | The exporter, on localhost only, sandboxed |
| Monitoring | [`grafana-override.conf`](monitoring/grafana-override.conf) | CT 108 `/etc/systemd/system/grafana-server.service.d/override.conf` | Grafana settings as environment variables |
| Monitoring | [`grafana-datasource.yaml`](monitoring/grafana-datasource.yaml) | CT 108 `/etc/grafana/provisioning/datasources/prometheus.yaml` | Prometheus as Grafana's default data source |
| Monitoring | [`grafana-dashboards.yaml`](monitoring/grafana-dashboards.yaml) | CT 108 `/etc/grafana/provisioning/dashboards/homelab.yaml` | Loads the dashboards kept as files |
| Monitoring | [`make-rules.py`](monitoring/make-rules.py) | Node `/root/monitoring/` | Writes the three Grafana alert rules |
| Monitoring | [`make-alerting.py`](monitoring/make-alerting.py) | Node `/root/monitoring/` | Writes the ntfy contact point and the notification policy |
| Monitoring | [`ntfy-payload.tmpl`](monitoring/ntfy-payload.tmpl) | Node `/root/monitoring/` | Grafana webhook payload: priority and tags by alert state |
| Alerting | [`ntfy-server.yml`](alerting/ntfy-server.yml) | CT 106 `/etc/ntfy/server.yml` | Deny-by-default ntfy server |
| Alerting | [`setup-ntfy.sh`](alerting/setup-ntfy.sh) | Node `/root/ntfy/` | Creates the topic, the publisher user and the tokens for Proxmox and Uptime Kuma; safe to re-run |
| Alerting | [`kuma-ntfy.js`](alerting/kuma-ntfy.js) | CT 105 `/opt/uptime-kuma/` | Attaches ntfy to two Uptime Kuma probes |
| Alerting | [`notification-matchers.cfg`](alerting/notification-matchers.cfg) | Node `/etc/pve/notifications.cfg` (matchers only) | Routes Proxmox notifications by severity |
| Alerting | [`smartd.conf`](alerting/smartd.conf) | Node `/etc/smartd.conf` (one line) | Disk alerts only when the bad-sector counters change |
| Inventory | [`netbox-configuration.py`](ipam/netbox-configuration.py) | CT 109 `/opt/netbox/netbox/netbox/configuration.py` | NetBox settings, secrets replaced by `<...>` |
| Inventory | [`nginx-netbox.conf`](ipam/nginx-netbox.conf) | CT 109 `/etc/nginx/sites-available/netbox` | nginx in front of gunicorn |
| Dashboard | [`services.yaml`](dashboard/services.yaml) | CT 110 `/opt/homepage/config/` | Homepage cards and widgets |
| Dashboard | [`settings.yaml`](dashboard/settings.yaml) | CT 110 `/opt/homepage/config/settings.yaml` | Homepage title, theme and layout; update check off |
| Dashboard | [`widgets.yaml`](dashboard/widgets.yaml) | CT 110 `/opt/homepage/config/widgets.yaml` | The clock in the top bar |
| Dashboard | [`bookmarks.yaml`](dashboard/bookmarks.yaml) | CT 110 `/opt/homepage/config/bookmarks.yaml` | Empty: no bookmarks |
| Dashboard | [`homepage.service`](dashboard/homepage.service) | CT 110 `/etc/systemd/system/` | Homepage on port 80 with Node.js 22 |
| Backups | [`jobs.cfg`](backups/jobs.cfg) | Node `/etc/pve/jobs.cfg` | The nightly backup job |
| Backups | [`vzdump.conf`](backups/vzdump.conf) | Node `/etc/vzdump.conf` (one line) | Runs the hook after every job |
| Backups | [`vzdump-hook`](backups/vzdump-hook) | Node `/usr/local/sbin/` | Calls `pve-latest-copy` when a job ends |
| Backups | [`pve-latest-copy`](backups/pve-latest-copy) | Node `/usr/local/sbin/` | Hard links to the newest backups, for Syncthing |
| Backups | [`pve-config-backup`](backups/pve-config-backup), [`.service`](backups/pve-config-backup.service), [`.timer`](backups/pve-config-backup.timer) | Node `/usr/local/sbin/`, `/etc/systemd/system/` | Nightly archive of `/etc`, `/root` and `/usr/local`, last 14 kept |
| Patching | [`20auto-upgrades`](patching/20auto-upgrades), [`52security-only`](patching/52security-only) | Every service container, `/etc/apt/apt.conf.d/` | Daily unattended upgrades, Debian security only |
| Firewall | [`cluster.fw`](firewall/cluster.fw) | Node `/etc/pve/firewall/cluster.fw` | The datacenter switch, the two IP sets, one alias per server, the `admin-access` and `panel-access` groups (one rule per monitoring flow) and the `local_network` override |
| Firewall | [`host.fw`](firewall/host.fw) | Node `/etc/pve/nodes/pve01/host.fw` | The node's own rules and options: the web UI and ping from my devices, the API from Prometheus and Homepage, nothing else |
| Firewall | [`100.fw`](firewall/100.fw) | Node `/etc/pve/firewall/100.fw` | Pi-hole: DHCP, DNS, NTP, ping and TCP 7 for everyone; its web interface only through the proxy |
| Firewall | [`105.fw`](firewall/105.fw) | Node `/etc/pve/firewall/105.fw` | Uptime Kuma: panel access plus the router's syslog |
| Firewall | [`106.fw`](firewall/106.fw) | Node `/etc/pve/firewall/106.fw` | ntfy: the same rules as the other panels |
| Firewall | [`ct-panel.fw`](firewall/ct-panel.fw) | Node `/etc/pve/firewall/1xx.fw` | The same file for CT 107 to CT 110: only the HTTPS proxy and the monitoring flows, SSH dropped |
| Firewall | [`ct-admin-only.fw`](firewall/ct-admin-only.fw) | Node `/etc/pve/firewall/102.fw` | Syncthing: admin access only, SSH dropped |
| Firewall | [`112.fw`](firewall/112.fw) | Node `/etc/pve/firewall/112.fw` | The HTTPS proxy: ports 443 and 80 from my devices |
| HTTPS | [`Caddyfile`](reverse-proxy/Caddyfile) | CT 112 `/etc/caddy/Caddyfile` | Caddy with its own certificate authority: one HTTPS name per panel, and the root certificate over plain HTTP |
