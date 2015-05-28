#!/usr/bin/python

import setup
setup.pre_install()
import consul
import json
import subprocess
import sys

from charmhelpers.core import hookenv, host
from charmhelpers import fetch
from path import path


hooks = hookenv.Hooks()
# The path to the consul configuration file.
CONF_FILE = path('/etc/consul.json')
# The path to the consul binary.
CONSUL = path('/usr/local/bin/consul')
# The path to the JSON file containing default configuration values.
DEFAULT_JSON = path(hookenv.charm_dir() + '/files/default.json')
# The path to the init configuration file for consul.
INIT_CONSUL = path('/etc/init/consul.conf')
# The library directory for consul.
LIB_DIRECTORY = path('/usr/lib/consul')
# The directory to place the consul binary.
LOCAL_BIN_DIRECTORY = path('/usr/local/bin')
# The ports to open for consul.
PORTS = [53, 8302, 8400, 8500]
# The directory for the consul web ui.
SHARE_DIRECTORY = path('/usr/share/consul')
# Consul upstart file.
UPSTART_FILE = path(hookenv.charm_dir() + '/files/consul.upstart')


@hooks.hook('install')
def install():
    ''' Juju calls the start hook after the charm is created. '''
    hookenv.log('Starting install hook.')
    # Install the software packages that will be used in this charm.
    apt_packages = ['git', 'python-pip', 'python-requests', 'unzip', 'wget']
    fetch.apt_install(fetch.filter_installed_packages(apt_packages))
    # Create the consul user and group.
    host.adduser('consul', shell='/sbin/nologin', system_user=True)
    # The lib directory is where consul files are written.
    host.mkdir(LIB_DIRECTORY, owner='consul', group='consul')
    # The share directory is for the web_ui
    host.mkdir(SHARE_DIRECTORY, owner='consul', group='consul')
    # Copy the upstart file to the init directory.
    UPSTART_FILE.copy(INIT_CONSUL)
    hookenv.log('The install hook finished.')


@hooks.hook('config-changed')
def changed():
    ''' Juju calls the config-changed hook when configuration changes. '''
    hookenv.log('Starting config-changed hook')
    # Get all the Juju configuration.
    config = hookenv.config()

    if not CONSUL.isfile() or config.changed('version'):
        version = config['version']
        hookenv.log('The version has changed, installing {0}'.format(version))
        consul.install_consul(version, LOCAL_BIN_DIRECTORY)
        consul.install_web_ui(version, SHARE_DIRECTORY)

    defaults = consul.get_defaults(DEFAULT_JSON)
    data = consul.configure_consul(defaults, config)
    changed = consul.has_changed(CONF_FILE, data)
    if changed:
        with open(CONF_FILE, 'w') as fh:
            fh.write(json.dumps(data, indent=2))
        print('Wrote config with \n%s' % (json.dumps(data, indent=2)))
    # Ensure the consul agent is running, restart if configuration changed.
    ensure_running(changed)

    hookenv.log('The config-changed hook finished.')


@hooks.hook('start')
def start():
    ''' Juju calls the start hook after after config-changed. Open ports. '''
    ensure_running(False)

    if host.service_running('consul'):
        for p in PORTS:
            hookenv.open_port(p)
    else:
        hookenv.log('The consul service is not running!', hookenv.WARNING)


@hooks.hook('stop')
def stop():
    ''' Juju calls the stop hook before the unit is destroyed.  Clean up. '''
    # Do we need to call explicitly call leave here?
    if host.service_running('consul'):
        host.service_stop('consul')
    for p in PORTS:
        hookenv.close_port(p)


@hooks.hook('cluster-relation-joined')
def cluster():
    ''' Called when a unit joins a cluster relationship. '''
    hookenv.log('Starting the cluster-relation-joined hook.')

    join_command = [CONSUL.abspath(), 'join']
    cluster_rid = hookenv.relation_ids('cluster')
    if cluster_rid:
        peers = hookenv.related_units(cluster_rid[0])
        if peers:
            for peer in peers:
                data = hookenv.relation_get(unit=peer, rid=cluster_rid[0])
                join_command.append(data.get('private-address'))
            hookenv.log(join_command)
            # Call the consul join command.
            output = subprocess.check_output(join_command)
            hookenv.log(output)
    else:
        hookenv.log('No peers to join with.')

    hookenv.log('The cluster-relation-joined hook finished.')


@hooks.hook('api-relation-joined')
def api():
    '''
    The api relation gives other charms the address and port of the consul
    api server. The main interface to Consul is a RESTful HTTP API.
    By default, the output of all HTTP API requests is minimized JSON. If the
    client passes pretty on the query string, formatted JSON will be returned.
    '''
    hookenv.log('Starting the api-relation-joined hook.')
    private_address = hookenv.unit_private_ip()
    hookenv.relation_set(address=private_address, port='8500')
    hookenv.log('The api-relation-joined hook finished.')


@hooks.hook('admin-relation-joined')
def admin():
    '''
    The admin relation gives other charms the hostname, port and url
    of the HTTP administrator interface for Consul.
    '''
    hookenv.log('Starting the admin-relation-joined hook.')
    admin_port = '8500'
    private_address = hookenv.unit_private_ip()
    ui_url='http://{0}:{1}/ui'.format(private_address, admin_port)
    hookenv.relation_set(hostname=private_address, port=admin_port, url=ui_url)
    hookenv.log('The admin-relation-joined finished.')


def ensure_running(changed):
    '''
    Reload the consul service if running and the configuration has changed,
    otherwise start the consul service.
    '''
    if host.service_running('consul'):
        if changed:
            print('Reloading the consul process.')
            # Reloading configuration does not reload all configuration items.
            # The items which are reloaded include: Log level, Checks,
            # Services, Watches, HTTP Client Address
            host.service_reload('consul', True)
        else:
            print('Consul server already running.')
        return
    print('Starting consul server.')
    host.service_start('consul')


if __name__ == '__main__':
    hooks.execute(sys.argv)
