# Troubleshooting case studies

Real incidents from this network, written up as investigations. The services they
involve are documented in [`docs/`](../docs/README.md).

| ID | Case | What it shows |
|---|---|---|
| [TSH-01](01-internet-outages.md) | The internet kept dropping after the server went in | Correlating logs from the router, the node and a client device; isolating the failing segment; ruling out the obvious suspect |
| [TSH-02](02-recursive-dns-nxdomain.md) | The new recursive resolver said real names did not exist | Comparing resolvers, QNAME minimization, a diagnosis revised by TSH-04 |
| [TSH-03](03-failing-system-ssd.md) | The system SSD started reallocating sectors | SMART attributes, alerting that only fires on change, backup strategy under a failing disk |
| [TSH-04](04-isp-intercepted-dns.md) | The root servers answered like a resolver | Reading DNS flags, probing an address where nothing should answer, proving DNS interception, DNS over TLS |
