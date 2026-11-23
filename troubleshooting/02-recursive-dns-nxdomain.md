# TSH-02 — The new recursive resolver said real names did not exist

## The report

On the afternoon Unbound replaced Google and Cloudflare as Pi-hole's upstream
([DNS](../docs/02-dns.md)), two problems came in: a streaming app stopped working on one device,
and a sign-in page would not load on another.

## Narrowing it down

**Blocked, or broken?** A blocked name answers `0.0.0.0`. These answered `NXDOMAIN`
("this name does not exist"), three times in a row, through Pi-hole only. The same
names resolved through `1.1.1.1` and `8.8.8.8`:

```text
<app>.api.edge.<domain-a>            an app's API (and three more names under that domain)
<host>.<domain-b>                    a second app
<id>.na.api.<domain-c>               the same second app
<host>.<domain-d>                    a cloud service
<id>.us-east-1.token.awswaf.com      the bot protection used by that sign-in page
```

In a sample of 55 common sites, only two names differed, both already on that list.
So the blocklist was not the cause, and most of the internet resolved fine.

**Ask the authoritative servers directly.** With the full name, the answers were correct.
With the shorter intermediate names, they came back `NXDOMAIN` or `SERVFAIL`:

```text
<app>.api.edge.<domain-a>          @<name server 1>         →  CNAME + 4 A records
api.edge.<domain-a>                @<servers 1 and 2>       →  SERVFAIL
api.edge.<domain-a>                @<servers 3 and 4>       →  NXDOMAIN
<id>.na.api.<domain-c>             @<its name server>       →  CNAME …
na.api.<domain-c>                  @<its name server>       →  SERVFAIL
```

## First diagnosis: QNAME minimization

**QNAME minimization looked like the cause.** To leak less, a resolver with this feature
does not send the full name to every server in the chain: it asks for one more label at
a time (`edge.<domain-a>`, then `api.edge.<domain-a>`, …). Those intermediate names
exist only as part of longer names. A compliant server answers `NOERROR` with no data
for them, and the replies above were `NXDOMAIN` or `SERVFAIL`, so the minimized queries
were taken to be what broke resolution. The full names resolved through `1.1.1.1` and
`8.8.8.8`, which seemed to agree.

The reasoning had a gap: Unbound does not stop at an error on a minimized query; it
asks again with the full name, except after an `NXDOMAIN` from a DNSSEC-signed zone.
Turning the feature off did make the names resolve; why the minimized queries failed
was never proven.

## Fix

One line in Unbound's configuration, then a syntax check and restarts:

```sh
pct exec 100 -- sh -c "printf '\n    qname-minimisation: no\n' >> /etc/unbound/unbound.conf.d/pi-hole.conf \
  && unbound-checkconf && systemctl restart unbound && /usr/local/bin/pihole restartdns"
```

Minutes later all eight names resolved through Pi-hole. Blocking and DNSSEC validation
still worked: `doubleclick.net` → `0.0.0.0`, `dnssec-failed.org` → `SERVFAIL`.

The second report itself was never confirmed in the query log; the names behind its
sign-in page failed the same way and resolved after the fix.

## The real cause

Three days later, [TSH-04](04-isp-intercepted-dns.md) found that the upstream network
answers every plain DNS query on port 53 itself, so Unbound's queries never reached the
root servers or the authoritative servers. The direct queries above, and the comparison
with `1.1.1.1` and `8.8.8.8`, went through the same path: every answer on this page came
from the ISP's resolver, and the fix worked without the diagnosis being right. Unbound
forwards to Quad9 over TLS ([DNS](../docs/02-dns.md)), where QNAME minimization has no
effect, so the `qname-minimisation: no` line changes nothing.

## Lessons

- Compare against a public resolver first: it separates "blocked" from "broken" in
  one step.
- When a resolver says a name does not exist, ask the authoritative servers yourself,
  with the full name and with the intermediate names, and check the `aa` flag: an
  answer without it did not come from them ([TSH-04](04-isp-intercepted-dns.md)).
- A fix that works does not prove the explanation. Write down what was proven and what
  was assumed.
