#!/usr/bin/python
import json
import os
import subprocess
import sys

from charmhelpers.core import hookenv, host


hooks = hookenv.Hooks()

CONF_PATH = "/etc/consul.json"
BIN_PATH = "/usr/local/bin/consul"
PORTS = [53, 8302, 8400, 8500]
LEADER_DATA = {'shared-key': 'shared_key'}


@hooks.hook(
    'config-changed',
    'start',
    'cluster-relation-changed',
    'cluster-relation-departed')
def changed():
    import pdb; pdb.set_trace()
    data = get_template_data()
    changed = write_config(data)

    if changed:
        print("Wrote config with \n %s" % (json.dumps(data, indent=2)))

    if not validate_config(data):
        return

    ensure_running(changed)
    rel = _raft_rel()

    if changed and rel:
        print("Rewriting config")
        hookenv.relation_set(rel, running='yes')
        for p in PORTS:
            hookenv.open_port(p)


@hooks.hook('stop')
def stop():
    if host.service_running('consul'):
        host.service_stop('consul')
    for p in PORTS:
        hookenv.close_port(p)


def validate_config(data):
    for k in LEADER_DATA:
        if not data.get(k):
            return False
    return True


def write_config(data):
    if os.path.exists(CONF_PATH):
        with open(CONF_PATH) as fh:
            contents = json.loads(fh.read())
    else:
        contents = {}

    if contents == data:
        return False

    with open(CONF_PATH, 'w') as fh:
        fh.write(json.dumps(data, indent=2))
    return True


def ensure_running(changed):
    if host.service_running('consul'):
        if changed:
            print("Reloaded consul config")
            subprocess.check_call([BIN_PATH, "reload"])
        else:
            print("Consul server already running")
        return
    print("Starting consul server")
    host.service_start('consul')


def get_template_data():
    data = get_leader_data()
    if data is None:
        return
    print("Leader data %s" % data)
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

    data['datacenter'] = os.environ.get("JUJU_ENV_NAME", "dc1")
    data['node_name'] = hookenv.local_unit().replace('/', '-')
    data['domain'] = config.get('domain')
    data['log_level'] = log_level.lower()

    return data


def get_leader_data():
    """Retrieve the current leader data.

    If needed, perform leader election.
    """
    result = {}
    leader = _leader()
    if leader is None:
        print("No leader found")
        return result
    if leader == hookenv.local_unit():
        print("Follow me")
        _follow_me()
        result['bootstrap'] = True
    else:
        print("Join cluster")
        peers = _peer_addrs()
        if not peers:
            print("No peers known.. exiting")
            return result
        result['start_join'] = peers
    data = hookenv.relation_get(unit=leader, rid=_raft_rel())
    for k, v in LEADER_DATA.items():
        result[k] = data.get(v)
    return result


@hookenv.cached
def _raft_rel():
    """Retrieve the cluster relation id if it exists."""
    leader_rel = hookenv.relation_ids('cluster')
    if not leader_rel:
        return None
    return leader_rel[0]


def _peers():
    """Get all the cluster peers."""
    leader_rel = _raft_rel()
    if not leader_rel:
        return []
    units = hookenv.related_units(leader_rel)
    return units


def _peer_addrs():
    """Get the address of all cluster peers."""
    addrs = []
    peers = _peers()
    rid = _raft_rel()
    print("Filtering peer addresses from %s" % peers)
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
    # Use a copy so we don't corrup the hookenv cache.
    units = list(units)
    units.append(local_unit)
    units.sort()
    leader = units.pop(0)
    print("Leader is %s followers are %s" % (
        leader, ",".join(units)))
    return leader


def _follow_me():
    """Elect self as the leader, and generate keys and certs."""
    data = hookenv.relation_get(
        unit=hookenv.local_unit(), rid=_raft_rel())
    if 'shared_key' in data:
        return data
    key = subprocess.check_output(
        ['/usr/local/bin/consul', 'keygen'])
    hookenv.relation_set(shared_key=key.strip())
    data['shared-key'] = key
    return data

if __name__ == '__main__':
    hooks.execute(sys.argv)
