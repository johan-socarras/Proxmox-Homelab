# TSH-01 — The internet kept dropping after the server went in

## The report

From the week the Proxmox server was installed, the internet at home kept dropping,
and it only came back after power-cycling the home router: ten times in eight days.
The obvious suspect was the new server.

## What the logs said

Three sources were lined up by timestamp: the Wi-Fi event log of a client
device, the kernel log of the node, and the router's own system log. Pi-hole's query log filled in the DNS side.

| Question | Finding |
|---|---|
| Did it start with the server? | Yes. In the previous two and a half months the client had three Wi-Fi drops of a few seconds. Since the server went in: nine router restarts in eight days by the time the logs were read (the tenth came that evening). |
| What fails? | The router. At every restart the node's cable link and the client's Wi-Fi drop in the same second and return 3–4 minutes later, with the router's boot signature. |
| Is the server causing it? | No. The node has a single NIC, so there is no loop, and its link never dropped before a router restart. Its NIC resets (`NETDEV WATCHDOG`) happen *during* the router's boot: an effect, not the cause. |
| Is Pi-hole causing it? | No. It received queries from the client until the last minute before each restart, and its upstream kept answering. No rate-limit warnings. |
| What does the router say? | In the months before, it ran 54, 53 and 20 days without a restart. Then 12 boots in 8 days: the ten power-cycles, a power cut that also restarted the node, and one more that the log does not explain. |
| What fails first? | In one event the router stopped answering on both cable and Wi-Fi 36 seconds before the link dropped: the router hung. In another, the client and Pi-hole kept retrying DNS while downloads on the server still completed: the way out was failing in part, not down. |
| Anything unusual upstream? | The home router sits behind the ISP's router (double NAT). |

## Instrumenting the next one

Instead of guessing, the next outage had to explain itself:

- **Probes for each segment** in Uptime Kuma: the router, Pi-hole, the router's DNS, the
  ISP gateway, two public IPs, public DNS, and HTTPS with and without DNS. The status
  page tells which segment failed ([Monitoring](../docs/04-monitoring.md)).
- **The router's syslog sent to the server.** The router only writes its own log to
  storage once an hour, so a hang erased what led up to it. With remote syslog, the
  lines are on another machine before the router goes down.

## Resolution

The same night, the router's **deep packet inspection** feature was turned off. The
router log shows the change at 23:41: the services it restarted include the inspection
engine. The last failure the probes recorded
was 40 minutes earlier, and the router has not dropped since.

Two days later the internet probes did fail again, for 26 minutes. That time the
router probe stayed green, which pointed away from the router: the cause was a lab
firewall VM that came up on the home network with its factory settings
([Labs](../docs/09-labs.md#lesson-learned-the-first-nic-is-the-lan)). The pattern of
green and red probes alone told the two problems apart.

The most likely cause is that inspecting every connection saturated the router
once a server added traffic of its own. This is inferred from
the timing, not measured.

**Trade-off:** the router no longer filters malicious sites by inspection. Pi-hole's
blocklist covers part of that by DNS, but it does not inspect traffic.

## Lessons

- "It started when X was installed" is a lead, not a conclusion. The timestamps showed
  the server was a witness, not the cause.
- Line up logs from several devices by time. The device that fails first is rarely the
  one that complains loudest.
- Get the logs off the device that hangs, before the next hang.
- Test the path one segment at a time, so an outage names its own location.
