# TSH-04 — The root servers answered like a resolver

## The report

A new Windows 11 client in the [labs](../docs/09-labs.md) could not activate:
`slmgr /ato` failed with `0x80072EE7`, a name that would not resolve. Every query to the
lab's DNS server, OPNsense at `10.10.10.1`, came back `SERVFAIL`, even `example.com`.
The same client could reach the internet by address.

## Narrowing it down

**Which resolver is failing?** OPNsense runs its own Unbound as a recursive resolver,
with no forwarders. With verbose logging, every query ended the same way:

```text
info: resolving example.net. A IN
debug: Failed to get a delegation, giving up
debug: return error response SERVFAIL
```

Unbound could not even learn the root zone. Its infrastructure cache had every root
server marked `rec 1`: their replies looked like a recursive resolver's, not like an
authoritative server's.

**Ask a root server directly**, from OPNsense:

```text
drill . SOA @198.41.0.4      →  flags: qr rd ra      (no aa)
```

A real root server answers with `aa` (authoritative) and without `ra` (recursion
available). This answer had them the other way round.

**Ask an address where there is no DNS server at all.** `203.0.113.77` is in a range
reserved for documentation; nothing should answer there:

```text
drill -u example.com @203.0.113.77   →  NOERROR, 2 answers
drill -t example.com @203.0.113.77   →  NOERROR, 2 answers
```

The same from another device on the home LAN, outside the lab. Something on the path answers
every DNS query on port 53, over UDP and TCP, whatever the destination address.

**Who answers?** A CHAOS-class `id.server` query to that same empty address returned
the host name of a caching name server belonging to the ISP, and `version.bind` came
back hidden. So the answers came from the ISP's resolver; what is less certain is where
on the path the queries were redirected to it. The home router gives no answer to
`version.bind` at its own address, and I found no DNS redirection option in its
settings, so the redirection most likely happens upstream of it, in a network I cannot
inspect. `whoami.akamai.net` returns the address of whichever resolver asks
Akamai's servers: asked through the Pi-hole, it returned an ISP resolver's address
instead of the home's public address.

## Root cause

Everything points to the upstream network, which I do not manage: it redirects all plain
DNS on port 53 to the ISP's resolvers. Two resolvers reacted differently:

- **OPNsense's Unbound** marked every root server as *recursion lame*: the replies
  carried `ra` and no `aa`, the signature of a resolver, not of an authoritative
  server. It refused to take a delegation from them, so it never got past the root
  zone: `SERVFAIL` for every name.
- **Pi-hole's Unbound** had been running as a recursive resolver for days, once QNAME
  minimization was off ([TSH-02](02-recursive-dns-nxdomain.md)), without a visible
  problem. The ISP's resolver validates DNSSEC and its answers were correct, so
  nothing failed; but every name was being resolved by the ISP, not from the root
  servers. Recursion was never really happening.

Why one Unbound rejected those replies and the other accepted them was not found. Their
versions and configurations were never compared, and by the time the question came up,
Pi-hole's Unbound had already stopped resolving from the root ([Fix](#fix)).

## Fix

Plain DNS cannot get past the interception, so the queries now leave encrypted:

1. **Pi-hole's Unbound forwards over TLS to Quad9** on port 853, checking the
   certificate name `dns.quad9.net` ([DNS](../docs/02-dns.md),
   [`unbound-forward-quad9.conf`](../configs/dns/unbound-forward-quad9.conf)). Port 853
   was not intercepted. Snapshot first; rollback is deleting that file and restarting
   Unbound.
2. **OPNsense's Unbound forwards to the Pi-hole** (*Query Forwarding*, all domains), so
   the labs get the same blocklist, validation and encrypted upstream as the house.

After the change, through the Pi-hole:

```text
proto.on.quad9.net  TXT   →  "dot"           (Quad9 received it over DNS over TLS)
whoami.akamai.net   A     →  no longer an ISP resolver's address
dnssec-failed.org   A     →  SERVFAIL        (validation still on)
doubleclick.net     A     →  0.0.0.0         (blocklist still on)
```

From the lab client, `example.com` and Microsoft's activation servers resolved, and
Windows activated.

## Lessons

- A resolver that works is not proof that it works the way it was designed. Check what
  the far end sees (`whoami.akamai.net`, `proto.on.quad9.net`), not only that names
  resolve.
- Query an address where nothing should answer. If something does, the network is
  intercepting DNS.
- Read the flags. `aa` from a root server is normal; `ra` from one means someone else is
  answering.
- The two resolvers failed differently on the same network. The stricter one exposed
  the problem the other had been hiding.
- This interception may also explain the failures in
  [TSH-02](02-recursive-dns-nxdomain.md), which happened before it was found.
