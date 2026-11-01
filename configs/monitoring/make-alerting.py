import json, os
# Home lab: write Grafana alerting provisioning for CT 108. JSON is valid YAML.
# Copy of /root/monitoring/make-alerting.py on pve01. It reads the ntfy topic and the Grafana token from /root/ntfy/,
# so the generated contact-points.yaml holds secrets and is not published here.
tpl = open('/root/monitoring/ntfy-payload.tmpl').read()
topic = open('/root/ntfy/topic').read().strip()
token = open('/root/ntfy/token-grafana').read().strip()
cp = {'apiVersion': 1, 'contactPoints': [{'orgId': 1, 'name': 'ntfy', 'receivers': [{
    'uid': 'ntfy-pve01', 'type': 'webhook', 'disableResolveMessage': False,
    'settings': {'url': 'http://<lan>.106/', 'httpMethod': 'POST', 'authorization_scheme': 'Bearer',
                 'authorization_credentials': token, 'payload': {'template': tpl.replace('$', '$$'), 'vars': {'topic': topic}}}}]}]}
pol = {'apiVersion': 1, 'policies': [{'orgId': 1, 'receiver': 'ntfy', 'group_by': ['grafana_folder', 'alertname'],
       'group_wait': '30s', 'group_interval': '5m', 'repeat_interval': '12h'}]}
def write(path, obj, mode):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    os.write(fd, ('# Home lab: Grafana alerting provisioning (JSON is valid YAML).\n' + json.dumps(obj, indent=1) + '\n').encode()); os.close(fd)
write('/root/monitoring/grafana-contact-points.yaml', cp, 0o600)
write('/root/monitoring/grafana-policies.yaml', pol, 0o644)
print('written')
