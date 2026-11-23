"""Write the three Grafana alert rules for pve01: container down, disk almost full, memory high.

Copy of /root/monitoring/make-rules.py on pve01. It writes /root/monitoring/grafana-rules.yaml,
which goes to /etc/grafana/provisioning/alerting/rules.yaml in CT 108. JSON is valid YAML.

Optional arguments: the memory threshold and how long it must last (default 0.90 and 10m),
so the alert can be tested end to end with a low threshold.
"""
import json
import sys

mem_threshold = float(sys.argv[1]) if len(sys.argv) > 1 else 0.90
mem_for = sys.argv[2] if len(sys.argv) > 2 else '10m'


def rule(uid, title, expr, threshold, for_, summary):
    """A rule that fires when the query in A stays above the threshold for for_."""
    return {'uid': uid, 'title': title, 'condition': 'C', 'for': for_, 'noDataState': 'OK', 'execErrState': 'Error',
            'isPaused': False, 'labels': {'severity': 'critical'}, 'annotations': {'summary': summary},
            'data': [
                {'refId': 'A', 'relativeTimeRange': {'from': 600, 'to': 0}, 'datasourceUid': 'prometheus',
                 'model': {'refId': 'A', 'expr': expr, 'instant': True, 'range': False}},
                {'refId': 'C', 'datasourceUid': '__expr__',
                 'model': {'refId': 'C', 'type': 'threshold', 'expression': 'A',
                           'conditions': [{'evaluator': {'type': 'gt', 'params': [threshold]}}]}}]}


# Each container metric is joined with pve_guest_info to get the container's name.
guests = 'on(id) group_left(name) pve_guest_info'
# Stopped containers, counted only when they are set to start at boot.
down = 'max by (id, name) ((pve_up{id=~"lxc/.*"} == bool 0) * ' + guests + ' * on(id) group_left() pve_onboot_status)'
disk = ('(pve_disk_usage_bytes{id=~"lxc/.*"} / pve_disk_size_bytes{id=~"lxc/.*"}) * ' + guests +
        ' or label_replace(pve_disk_usage_bytes{id=~"node/.*|storage/.*"} / pve_disk_size_bytes{id=~"node/.*|storage/.*"}, "name", "$1", "id", "(?:node|storage/[^/]+)/(.+)")')
mem = ('(pve_memory_usage_bytes{id=~"lxc/.*"} / pve_memory_size_bytes{id=~"lxc/.*"}) * ' + guests +
       ' or label_replace(pve_memory_usage_bytes{id=~"node/.*"} / pve_memory_size_bytes{id=~"node/.*"}, "name", "$1", "id", "node/(.+)")')

rules = {'apiVersion': 1, 'groups': [{'orgId': 1, 'name': 'pve01', 'folder': 'Home lab', 'interval': '1m', 'rules': [
    rule('pve-container-down', 'Container down', down, 0, '2m',
         'Container {{ $labels.name }} ({{ $labels.id }}) is stopped and should be running'),
    rule('pve-disk-almost-full', 'Disk almost full', disk, 0.85, '10m',
         'Disk of {{ $labels.name }} ({{ $labels.id }}) is {{ humanizePercentage $values.A.Value }} full'),
    rule('pve-memory-high', 'Memory high', mem, mem_threshold, mem_for,
         'Memory of {{ $labels.name }} ({{ $labels.id }}) is at {{ humanizePercentage $values.A.Value }}')]}]}

# Grafana does not expand $ in rule files (it does in contact points), so $labels stays as it is.
with open('/root/monitoring/grafana-rules.yaml', 'w') as f:
    f.write('# Home lab: Grafana alert rules for pve01 (JSON is valid YAML).\n' + json.dumps(rules, indent=1) + '\n')
print('rules written, memory', mem_threshold, mem_for)
