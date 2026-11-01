# Copy of /opt/netbox/netbox/netbox/configuration.py in CT 109 (netbox.lan), with the secrets replaced by <...>.
# Home lab: generated on pve01 by /root/netbox/make-config.py from
# /root/netbox/{db-password,secret-key,token-pepper}; the secrets exist only in this file on CT 109 and in /root/netbox.
ALLOWED_HOSTS = ['netbox.lan', '<lan>.109', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['https://netbox.lan']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'netbox',
        'USER': 'netbox',
        'PASSWORD': '<db-password>',
        'HOST': 'localhost',
        'PORT': '',
        'CONN_MAX_AGE': 300,
    }
}
REDIS = {
    'tasks': {'HOST': 'localhost', 'PORT': 6379, 'USERNAME': '', 'PASSWORD': '', 'DATABASE': 0, 'SSL': False},
    'caching': {'HOST': 'localhost', 'PORT': 6379, 'USERNAME': '', 'PASSWORD': '', 'DATABASE': 1, 'SSL': False},
}
SECRET_KEY = '<secret-key>'
API_TOKEN_PEPPERS = {1: '<token-pepper>'}
# Anyone on the LAN can browse; changes need a login.
LOGIN_REQUIRED = False
# What anonymous visitors may see: the inventory, never users, tokens or permissions.
EXEMPT_VIEW_PERMISSIONS = [
    'dcim.site', 'dcim.manufacturer', 'dcim.devicetype', 'dcim.devicerole', 'dcim.device', 'dcim.interface', 'dcim.macaddress',
    'ipam.prefix', 'ipam.iprange', 'ipam.ipaddress',
    'tenancy.tenant',
    'virtualization.clustertype', 'virtualization.cluster', 'virtualization.virtualmachine', 'virtualization.vminterface', 'virtualization.virtualdisk',
    'extras.tag',
]
# Nothing leaves the home network.
CENSUS_REPORTING_ENABLED = False
ISOLATED_DEPLOYMENT = True
TIME_ZONE = '<timezone>'
