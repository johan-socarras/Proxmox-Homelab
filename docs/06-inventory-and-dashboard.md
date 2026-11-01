# Inventory and dashboard: NetBox and Homepage

## NetBox: the inventory of the network

### What it does

NetBox is the source of truth for the home network: every subnet, address, device,
MAC address and container is recorded there. Before a new service gets a static
address, the free addresses are checked in NetBox.

### How it is built

- **CT 109 `netbox`**: NetBox 4.7 from the official release tarball, PostgreSQL 17 and
  Redis 8 from Debian, gunicorn with two workers behind nginx on port 80
  ([`configs/ipam/`](../configs/ipam/)).
- **What it holds:**
  - the home prefix and the Tailscale prefix (`100.64.0.0/10`);
  - Pi-hole's DHCP pool, recorded as an IP range, so static addresses stay out of it;
  - every household device, with its MAC address, IP address, `.lan` name and its
    Pi-hole client group as a tag;
  - `pve01` as a device, and every container as a virtual machine with its vCPUs,
    memory, disk, interface, MAC address and IP address;
  - the lab networks (`10.10.10.0/24`, `10.10.20.0/24`, `10.152.128.0/18`) with
    OPNsense's DHCP pools, and every lab machine, container or VM, with role `Lab`, its
    interfaces, bridges, disks and addresses. They are recorded as offline because they
    only run during a lab session.
- **Loaded by script.** One script collects the containers from the Proxmox API; another
  runs inside the NetBox container, through NetBox's Django shell, and writes
  everything into the inventory. A second loader, run the same way, adds the labs.
  Objects are matched by name, so running them again updates records instead of
  duplicating them. (The loaders are not published: they hold the household's device
  list and the MAC addresses.)
- **Access:** the devices the [firewall](10-firewall.md) lets in can browse the
  inventory without logging in, but not
  users, tokens or permissions (`EXEMPT_VIEW_PERMISSIONS`). Changes need the admin
  login. `ISOLATED_DEPLOYMENT` and no census reporting: it never contacts the internet.

### Why this way

An address plan that lives in someone's head breaks the first time two things get the
same address. NetBox does not scan the network; it is a record. Whoever changes the
network updates it, the same way a network team keeps its IPAM.

## Homepage: one page for everything

### What it does

`https://homepage.lan` is the start page of the homelab: a card per service, with a
link and a green or red status dot, plus live numbers where the service allows it.

### How it is built

- **CT 110 `homepage`**: Homepage 2.5, built from source, running on the official
  Node.js 22 LTS in `/opt/node` ([`configs/dashboard/`](../configs/dashboard/)).
  Debian 13 ships Node.js 20.19, and Homepage 2.5.0 needs 22: its locked dependencies
  ask for it (`undici` 8, pulled in by `@kubernetes/client-node`, needs 22.19 or later),
  its own Docker image is built on Node 22, and the build failed on Debian's Node 20.
  Being outside apt, Node.js gets no automatic security updates; it is updated by hand
  ([Patching](08-patching.md)).
- **Three groups:**
  - *Infrastructure*: Proxmox, with CPU, memory and running containers; Pi-hole; the router.
  - *Monitoring*: Grafana; Prometheus, with targets up and down; Uptime Kuma, with
    probes up and down; ntfy.
  - *Tools*: NetBox and Syncthing.
- **Its own read-only Proxmox token** (`homepage@pve!dashboard`; the user has the
  `PVEAuditor` role and the token inherits it). It sits in an environment file in the
  container and is used server-side; it never reaches the browser.
- **No requests to the internet:** icons are served from the container, and update
  checks and Next.js telemetry are off.

## How to verify

On the node:

```sh
pct exec 109 -- systemctl is-active netbox netbox-rq nginx postgresql redis-server
# active x5
pct exec 110 -- systemctl is-active homepage                   # active
```

From one of my devices:

```sh
curl -s https://netbox.lan/api/status/ | grep -o '"netbox-version":"[^"]*"'
curl -s https://netbox.lan/api/virtualization/virtual-machines/ | grep -o '"count":[0-9]*'
# one record per container and per lab machine
curl -s 'https://netbox.lan/api/virtualization/virtual-machines/?role=lab' | grep -o '"count":[0-9]*'
# "count":7   (VM 200, CT 201, VM 210, VM 211, VM 220, VM 230, VM 231)
curl -s -o /dev/null -w '%{http_code}\n' https://homepage.lan   # 200
```
