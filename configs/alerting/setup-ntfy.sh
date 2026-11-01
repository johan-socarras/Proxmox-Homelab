#!/bin/sh
# Home lab: configure ntfy in CT 106 for pve01 alerts.
# Creates a random topic name (/root/ntfy/topic), a write-only publisher user and one access token per sender
# (/root/ntfy/token-<sender>). Safe to re-run: existing topic and tokens are kept.
set -e
CT=106
D=/root/ntfy
umask 077
pct exec $CT -- install -d -o ntfy -g ntfy /var/cache/ntfy /var/lib/ntfy
pct exec $CT -- sh -c 'test -f /etc/ntfy/server.yml.dist || cp /etc/ntfy/server.yml /etc/ntfy/server.yml.dist'
pct push $CT $D/server.yml /etc/ntfy/server.yml --perms 0644
pct exec $CT -- systemctl enable ntfy >/dev/null 2>&1
pct exec $CT -- systemctl restart ntfy
sleep 2
[ -s $D/topic ] || echo "pve01-alerts-$(head -c 12 /dev/urandom | base32 | tr -d '=' | tr 'A-Z' 'a-z')" > $D/topic
TOPIC=$(cat $D/topic)
if ! pct exec $CT -- ntfy user list 2>&1 | grep -q 'user alerts-publisher'; then
  pct exec $CT -- env NTFY_PASSWORD="$(head -c 24 /dev/urandom | base64 | tr -d '/+=')" ntfy user add alerts-publisher >/dev/null
fi
pct exec $CT -- ntfy access alerts-publisher "$TOPIC" write-only >/dev/null
pct exec $CT -- ntfy access everyone "$TOPIC" read-only >/dev/null
for s in proxmox uptime-kuma; do
  [ -s $D/token-$s ] || pct exec $CT -- ntfy token add --label="$s" alerts-publisher | grep -o 'tk_[A-Za-z0-9]*' > $D/token-$s
done
echo "topic length: $(wc -c < $D/topic)"; for s in proxmox uptime-kuma; do echo "token-$s length: $(wc -c < $D/token-$s)"; done
