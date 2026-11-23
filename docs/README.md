# Documentation

One page per area, numbered in reading order. The overview and the network map are in
the [README](../README.md).

| # | Page | What it covers |
|---|---|---|
| 01 | [Node and storage](01-node-and-storage.md) | The hardware, the disk layout and the conventions every container follows |
| 02 | [DNS: Pi-hole and Unbound](02-dns.md) | How queries are filtered and encrypted, why it forwards over TLS instead of recursing, and DHCP on Pi-hole |
| 03 | [Remote access: Tailscale](03-remote-access.md) | A TUN device in an unprivileged container, DNS for the tailnet and the policy that limits who gets in |
| 04 | [Monitoring: Uptime Kuma, Prometheus and Grafana](04-monitoring.md) | The nine segment probes and how to read them, the exporter's read-only token, the three alert rules |
| 05 | [Alerting: ntfy](05-alerting.md) | Deny-by-default ntfy, one token per sender, and routing by severity |
| 06 | [Inventory and dashboard: NetBox and Homepage](06-inventory-and-dashboard.md) | What NetBox records and how it is loaded, and Homepage's cards and read-only token |
| 07 | [Backups](07-backups.md) | The nightly job and its retention, the configuration archive, the one-way copy and the restore test |
| 08 | [Patching](08-patching.md) | Unattended security updates, and the version and update method of every piece of software |
| 09 | [Labs: OPNsense and Active Directory](09-labs.md) | The lab bridges, OPNsense's rules, the domain and the offline domain join |
| 10 | [Firewall: admin access only from my devices](10-firewall.md) | IP sets and groups, HTTPS for the panels, one rule per monitoring flow, no SSH and the lost-reset workaround |
| 11 | [Lab: Browser sandbox](11-browser-sandbox.md) | A diskless VM behind two firewalls, with DNS pinned to Pi-hole |
| 12 | [Lab: Tor isolation with Whonix](12-tor-isolation.md) | The Whonix Gateway and Workstation, their firewall rules and the packet captures |

The real incidents behind some of these pages are written up in
[`troubleshooting/`](../troubleshooting/README.md), and the configuration files they link
to are in [`configs/`](../configs/README.md).
