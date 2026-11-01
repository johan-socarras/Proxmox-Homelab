import json, sys
# Home lab: Grafana alert rules for pve01 (CT 108). Args: memory threshold and memory "for" (normal: 0.90 10m).
# Copy of /root/monitoring/make-rules.py on pve01; it writes /root/monitoring/grafana-rules.yaml, which goes to
# /etc/grafana/provisioning/alerting/rules.yaml in CT 108.
mem_thr = float(sys.argv[1]) if len(sys.argv) > 1 else 0.90
mem_for = sys.argv[2] if len(sys.argv) > 2 else '10m'
def rule(uid, title, expr, thr, for_, summary):
    return {'uid': uid, 'title': title, 'condition': 'C', 'for': for_, 'noDataState': 'OK', 'execErrState': 'Error',
            'isPaused': False, 'labels': {'severity': 'critical'}, 'annotations': {'summary': summary},
            'data': [
                {'refId': 'A', 'relativeTimeRange': {'from': 600, 'to': 0}, 'datasourceUid': 'prometheus',
                 'model': {'refId': 'A', 'expr': expr, 'instant': True, 'range': False}},
                {'refId': 'C', 'datasourceUid': '__expr__',
                 'model': {'refId': 'C', 'type': 'threshold', 'expression': 'A',
                           'conditions': [{'evaluator': {'type': 'gt', 'params': [thr]}}]}}]}
guests = 'on(id) group_left(name) pve_guest_info'
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
    rule('pve-memory-high', 'Memory high', mem, mem_thr, mem_for,
         'Memory of {{ $labels.name }} ({{ $labels.id }}) is at {{ humanizePercentage $values.A.Value }}')]}]}
# Rule files are not expanded by Grafana (contact points are), so $ stays as it is.
text = json.dumps(rules, indent=1)
open('/root/monitoring/grafana-rules.yaml', 'w').write('# Home lab: Grafana alert rules for pve01 (JSON is valid YAML).\n' + text + '\n')
print('rules written, memory', mem_thr, mem_for)
