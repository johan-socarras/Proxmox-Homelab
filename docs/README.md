# Documentation

One page per area, numbered in reading order. Each page explains what a service does,
how it is built, why it is built that way, and how to verify it. The overview and the
diagram of the whole server are in the [README](../README.md).

| # | Page | What it covers |
|---|---|---|
| 01 | [Node and storage](01-node-and-storage.md) | `pve01`, the only server: the hypervisor, its two disks and the containers every service runs in |
| 02 | [DNS: Pi-hole and Unbound](02-dns.md) | DNS and DHCP for the whole network: blocklist, local `.lan` names, DNSSEC, encrypted upstream (DNS over TLS) |
| 03 | [Remote access: Tailscale](03-remote-access.md) | Subnet router and exit node: the home network reachable from anywhere without opening a single port |
| 04 | [Monitoring: Uptime Kuma, Prometheus and Grafana](04-monitoring.md) | Probes for each network segment, 30 days of node and container metrics, dashboards and alert rules |
| 05 | [Alerting: ntfy](05-alerting.md) | Self-hosted push notifications to my devices, routed by severity |
| 06 | [Inventory and dashboard: NetBox and Homepage](06-inventory-and-dashboard.md) | IP address and device inventory, and a start page with the live status of every service |
| 07 | [Backups](07-backups.md) | Nightly backups with daily, weekly and monthly copies, and the newest ones synced to another device at home |
| 08 | [Patching](08-patching.md) | Automatic security updates for the containers, and what is updated by hand |
| 09 | [Labs: OPNsense and Active Directory](09-labs.md) | The lab networks behind an OPNsense firewall, with an Active Directory domain |
| 10 | [Firewall: admin access only from my devices](10-firewall.md) | Who can reach the management side of the server, HTTPS for the panels, one rule per flow |
| 11 | [Lab: Browser sandbox](11-browser-sandbox.md) | A diskless browser for untrusted sites, DNS pinned to Pi-hole |
| 12 | [Lab: Tor isolation with Whonix](12-tor-isolation.md) | Tor browsing with a Whonix Gateway and a Workstation that has no route except the gateway |

The real incidents behind some of these pages are written up in
[`troubleshooting/`](../troubleshooting/README.md), and the configuration files they link
to are in [`configs/`](../configs/README.md).
