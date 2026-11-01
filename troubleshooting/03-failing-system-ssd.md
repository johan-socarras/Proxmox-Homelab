# TSH-03 — The system SSD started reallocating sectors

## How it was found

Not from an alert. While reading the node's journal for
[TSH-01](01-internet-outages.md), smartd's messages about the system disk turned up.
That disk is a SATA SSD holding Proxmox and every container:

| SMART attribute | Value |
|---|---|
| 5 `Reallocated_Sector_Ct` | 16 |
| 197 `Current_Pending_Sector` | 16 |
| 198 `Offline_Uncorrectable` | 1 |
| Overall health | `PASSED`, 99 % life left |

The values had been there since the first line of the journal. `PASSED` only means
that no attribute has crossed the vendor's failure threshold; it does not mean the
disk is healthy.

## The second problem: no alert had ever left the server

- Postfix could not deliver mail to `root`, because `/etc/aliases.db` was missing:
  about 1,500 errors in a week, all silent.
- Proxmox's notifications pointed at an external mailbox that never received a single
  message.

So smartd had been warning into the void. Alerting was rebuilt from scratch on a
self-hosted ntfy server ([Alerting](../docs/05-alerting.md)): `newaliases` restored
local mail, root's mail now becomes a Proxmox notification, and Proxmox sends it to
my devices.

## Making the alert worth reading

By default smartd repeats the same warning at every boot, and a notification that arrives
every day about the same numbers gets ignored. The `DEVICESCAN` line in
`/etc/smartd.conf` now reports only changes:

```text
-C 197+    alert when Current_Pending_Sector increases
-U 198+    alert when Offline_Uncorrectable increases
-R 5!      alert when Reallocated_Sector_Ct changes
```

## The first real alert

The first change in nine days came on a morning of heavy writes, with four new
containers being installed: `Reallocated_Sector_Ct` went from 16 to 17, and the
pending count followed. smartd
sent a high-priority alert, *SMART error (Usage) detected on host: pve01*, which
reached me away from home through Tailscale. Health was still `PASSED`, with no
read or write errors in the kernel log.

## Decision

Treat the disk as failing:

- Backups went from weekly to **daily**, with 7 daily, 4 weekly and 3 monthly copies,
  on the other SSD ([Backups](../docs/07-backups.md)).
- A full manual backup of every container ran right after the alert, so that day's
  work did not depend on the disk.
- The newest backups now leave the server every night.
- Because the problem was caught early, the disk will be replaced soon, while it still
  works.
- Replacing the disk means reinstalling Proxmox and restoring from these backups.
  Restoring one container from a nightly backup has been tested: it started, and its
  service answered ([Backups](../docs/07-backups.md#tested)). Rebuilding the whole node
  has not been tested yet.

## Lessons

- SMART `PASSED` is a threshold, not a diagnosis. Read the raw attributes.
- Test the alert path end to end. Here it had never worked, and nobody knew.
- An alert should fire on change, or it becomes noise.
- A failing disk is a backup problem first and a hardware problem second.
