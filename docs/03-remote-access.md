# Remote access: Tailscale

## What it does

From anywhere, my devices can reach the home network as if they were at home, and they
use Pi-hole for DNS, so their lookups keep the home blocklist on any network. With the
exit node selected, all of their internet traffic leaves through the house as well.

## How it is built

- **CT 101 `tailscale-vpn`**, unprivileged, at `<lan>.101`, starts at boot. Tailscale comes
  from Tailscale's own Debian repository.
- **A TUN device inside an unprivileged container.** WireGuard needs `/dev/net/tun`,
  which an unprivileged container does not have by default; two lines in the
  container's configuration pass it through
  ([`configs/remote-access/lxc-101-tun.conf`](../configs/remote-access/lxc-101-tun.conf)).
- **IP forwarding** for IPv4 and IPv6 in
  [`/etc/sysctl.d/99-tailscale.conf`](../configs/remote-access/99-tailscale.conf).
- **Advertised routes:** the home subnet `<lan>.0/24` and the exit node (`0.0.0.0/0`,
  `::/0`). Both are approved in the Tailscale admin console, and key expiry is
  disabled for this node so it does not drop off the tailnet.
- **DNS for the tailnet:** the global nameserver is Pi-hole, with *Override DNS servers*
  on, so every device on the tailnet uses it, and with *Use with exit node* on, so it
  stays the resolver when the exit node is selected (without it, Tailscale would hand DNS
  to the exit node). Pi-hole sees those queries coming from CT 101 and applies the
  blocklist to them.
- **Source NAT stays on** (the default): traffic from the tailnet reaches LAN devices
  with the container's address, so they need no return route.
- **A tailnet policy that names who may use it**
  ([`tailnet-policy.hujson`](../configs/remote-access/tailnet-policy.hujson)). Tailscale's
  default policy lets every device in the tailnet reach every other one and every
  advertised route. Mine has three grants, all for `autogroup:owner`, the tailnet owner,
  which is me: my devices reach each other, use the subnet route to `<lan>.0/24`, and use
  the exit node (`autogroup:internet`). Nobody else is named, so an invited user, a device
  shared into the tailnet or a tagged device gets nothing. The tailnet's DNS server is
  Pi-hole, inside the subnet route, so MagicDNS keeps working for my devices.
- **Tests in the policy.** Tailscale runs them on every save and refuses a policy that
  fails one. One checks that I still reach DNS, the HTTPS proxy, the Proxmox web UI, the
  internet through the exit node and my own devices; the other checks that any other user
  reaches none of them.

## Why this way

- **No open ports.** The home router sits behind the ISP's router (double NAT), so
  classic port forwarding would need changes on both. Tailscale connects out and
  traverses NAT, and nothing on the router is exposed to the internet.
- **In a container, not on the host.** It is isolated from the hypervisor, and it is
  backed up and restored like every other service.
- **Exit node, not only a subnet route.** The subnet route and the tailnet's DNS
  settings already give my devices the home LAN and Pi-hole's filtering. The exit node
  adds the rest of their traffic: it leaves through home, so an outside network or a public
  Wi-Fi sees only the encrypted tunnel, and websites see the home address.
- **The policy, because of source NAT.** Everything from the tailnet reaches the LAN as
  CT 101, an address the [firewall](10-firewall.md) trusts like my own devices. Without a
  policy, anything that joins the tailnet would inherit that trust; with it, only my
  devices get as far as CT 101 in the first place.

## Tested

From an outside network, away from the home Wi-Fi, with the exit node selected:

- the device showed the home public IP address;
- `homepage.lan` opened on it;
- the node listed it as a direct peer-to-peer connection, not relayed;
- in six minutes Pi-hole logged 181 queries from the VPN container, 68 of them blocked.

After the tailnet policy went in, the same test from an outside network again showed the home
address, and `homepage.lan` and a panel opened through the HTTPS proxy. The policy's
own tests passed on save: my user reaches DNS, the proxy, the Proxmox web UI, the
internet through the exit node and my own devices, and any other user reaches none of
them.

## How to verify

On the node:

```sh
pct exec 101 -- tailscale status
# the node itself, with "offers exit node"
pct exec 101 -- tailscale debug prefs | grep -A4 AdvertiseRoutes
# 0.0.0.0/0, ::/0 and <lan>.0/24
pct exec 101 -- sysctl -n net.ipv4.ip_forward net.ipv6.conf.all.forwarding
# 1 and 1
```

On a device away from home, with the exit node on, an IP lookup such as
`https://1.1.1.1/cdn-cgi/trace` must show the same `ip=` as a device at home.

In the admin console, *Access controls → Preview rules* for my user lists exactly the
three grants (`autogroup:self`, `<lan>.0/24`, `autogroup:internet`), and *Tests* lists
the two tests that every save must pass.
