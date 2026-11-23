"""Write the Grafana alerting provisioning for CT 108: the ntfy contact point and the notification policy.

Copy of /root/monitoring/make-alerting.py on pve01. It reads the ntfy topic and the Grafana token
from /root/ntfy/, so the contact points file it writes holds secrets and is not published here.
JSON is valid YAML.
"""
import json
import os


def read(path):
    with open(path) as f:
        return f.read()


template = read('/root/monitoring/ntfy-payload.tmpl')
topic = read('/root/ntfy/topic').strip()
token = read('/root/ntfy/token-grafana').strip()

contact_points = {'apiVersion': 1, 'contactPoints': [{'orgId': 1, 'name': 'ntfy', 'receivers': [{
    'uid': 'ntfy-pve01', 'type': 'webhook', 'disableResolveMessage': False,
    'settings': {'url': 'http://<lan>.106/', 'httpMethod': 'POST', 'authorization_scheme': 'Bearer',
                 'authorization_credentials': token,
                 # Grafana expands $ in contact point files; $$ keeps the template's own variables.
                 'payload': {'template': template.replace('$', '$$'), 'vars': {'topic': topic}}}}]}]}
policies = {'apiVersion': 1, 'policies': [{'orgId': 1, 'receiver': 'ntfy', 'group_by': ['grafana_folder', 'alertname'],
            'group_wait': '30s', 'group_interval': '5m', 'repeat_interval': '12h'}]}


def write(path, obj, mode):
    """Write obj as JSON to a file created with the given permissions."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write('# Home lab: Grafana alerting provisioning (JSON is valid YAML).\n' + json.dumps(obj, indent=1) + '\n')


write('/root/monitoring/grafana-contact-points.yaml', contact_points, 0o600)
write('/root/monitoring/grafana-policies.yaml', policies, 0o644)
print('written')
