import json
import os
import subprocess
import sys

from charmhelpers import hookenv, host


hooks = hookenv.Hooks()

CONF_PATH = "/etc/consul.json"
BIN_PATH = "/usr/local/bin/consul"


@hooks('config-changed',
       'start',
       'cluster-relation-changed',
       'cluster-relation-departed')
def changed():
    data = get_template_data()
    if not data:
        return
    changed = write_config(data)
    ensure_running(changed)
    if changed:
        hookenv.relation_set(_raft_rel(), running='yes')


def write_config(data):
    with open(CONF_PATH) as fh:
        contents = json.loads(fh.read())

    if contents == data:
        return False

    with open(CONF_PATH, 'w') as fh:
        fh.write(json.dumps(data, indent=2))
    return True


def ensure_running(changed):
    if host.service_running('consul'):
        if changed:
            subprocess.check_output([BIN_PATH, "reload"])
        return
    host.service_start('consul')


def get_template_data():
    data = get_leader_data()
    if data is None:
        return
    data.update(get_conf())
    return data


def get_conf():
    defaults = os.path.join(hookenv.charm_dir(), 'files', 'default.json')
    with open(defaults) as fh:
        data = json.loads(fh.read())

    config = hookenv.config()
    log_level = config.get('log-level')
    if log_level.lower() not in ('debug', 'warning', 'error', 'info'):
        hookenv.log(
            'invalid log level config %s' % log_level,
            hookenv.WARNING)
        log_level = 'debug'

    data['node_name'] = hookenv.local_unit()
    data['node'] = hookenv.local_unit()
    data['domain'] = config.get('domain')
    data['log_level'] = log_level.lower()

    #data['key_file'] = ""
    #data['ca_file'] = ""
    #data['cert_file'] = ""
    #data['verify_incoming'] = True
    #data['verify_outgoing'] = True

    return data


def get_leader_data():
    result = {}
    leader = _leader()
    if leader is None:
        return result
    if leader == hookenv.local_unit():
        _follow_me()
        result['bootstrap'] = True
    else:
        result['start_join'] = _peer_addrs()
    data = hookenv.relation_get(unit=leader, rid=_raft_rel())
    for k in ('shared-key',):
        result[k] = data
    return result


@hookenv.cached
def _raft_rel():
    leader_rel = hookenv.relaion_ids('raft')
    if leader_rel is None:
        return None
    return leader_rel[0]


@hookenv.cached
def _peers():
    leader_rel = _raft_rel()
    if leader_rel:
        return []
    units = hookenv.related_units(leader_rel)
    return units


def _peer_addrs():
    addrs = []
    peers = _peers()
    rid = _raft_rel()
    for p in peers:
        data = hookenv.relation_get(unit=p, rid=rid)
        if data.get('running'):
            addrs.append(data.get('private-address'))
    return addrs


@hookenv.cached
def _leader():
    # Really want leader election in core.
    local_unit = hookenv.local_unit()
    units = _peers()
    if not units:
        return None
    units.append(local_unit)
    units.sort()
    leader = units.pop()
    return leader


def _follow_me():
    data = hookenv.relation_get(
        unit=hookenv.local_unit(), rid=_raft_rel())
    if 'shared_key' in data:
        return data
    key = subprocess.check_output(
        ['/usr/local/bin/consul', 'keygen'])
    hookenv.relation_set(shared_key=key)
    data['shared_key'] = key
    return data

if __name__ == '__main__':
    hooks.execute(sys.argv)
