#!/usr/bin/env python

import os
import json

from charmhelpers.core import hookenv
from charmhelpers.fetch import archiveurl
from path import path


# The path to the JSON file containing default configuration values.
DEFAULT_JSON = path(hookenv.charm_dir() + '/files/default.json')
# The url prefix to download consul release files.
URL_PREFIX = 'https://dl.bintray.com/mitchellh/consul/'
CONF_PATH = path('/etc/consul.json')


def consul_arch():
    ''' Generate the consul string based on platform values of this system. '''
    import platform
    # Find the system type string and convert to lower case.
    system = platform.system().lower()
    # Consul builds are only available for 'darwin' and 'linux'
    if system in ['darwin', 'linux']:
        machine = platform.machine()
        # Consul builds are only available for 'amd64' and '386'
        if machine == 'x86_64':
            package_arch = 'amd64'
        elif machine == 'i386':
            package_arch = '386'
        else:
            raise Exception('Invalid machine type: {0}'.format(machine))
        if package_arch:
            architecture = '{0}_{1}'.format(system, package_arch)
            return architecture
    else:
        raise Exception('Invalid system type: {0}'.format(system))


def install_consul(version, destination_directory='/usr/local/bin'):
    ''' Install the configured version of consul for the architecture. '''
    if version:
        architecture = consul_arch()
        consul_file_name = '{0}_{1}.zip'.format(version, architecture)
        url = URL_PREFIX + consul_file_name
        installer = archiveurl.ArchiveUrlFetchHandler()
        # Download and unzip the archive into the final destination directory.
        installer.install(url, dest=destination_directory)
        # TODO verify the sha256sum of the zip file!
        consul = path(destination_directory + '/consul')
        # Make the consul binary executable.
        consul.chmod(0o555)


def install_web_ui(version, destination_directory='/usr/share/consul'):
    ''' Install the configured version of consul web ui. '''
    if version:
        web_ui_name = '{0}_web_ui.zip'.format(version)
        url = URL_PREFIX + web_ui_name
        installer = archiveurl.ArchiveUrlFetchHandler()
        # Download and unzip the web ui to the share directory.
        installer.install(url, dest=destination_directory)
        # TODO verify the sha256sum of the zip file!


def has_changed(file, data):
    ''' Return True if the data object differs the JSON in the file. '''
    if os.path.exists(file):
        with open(file) as fh:
            contents = json.loads(fh.read())
    else:
        contents = {}

    return contents != data


def get_defaults(default_file):
    ''' Load the default values for consul from a JSON file. '''
    if os.path.exists(default_file):
        with open(default_file) as fh:
            defaults = json.loads(fh.read())
    else:
        defaults = {}
    return defaults


def configure_consul(defaults, config):
    '''
    Read the default JSON file from the charm directory, get the current
    configuration values, set the appropriate consul values, and return the
    data object.
    '''
    log_level = config.get('log-level')
    # The available log levels are "trace", "debug", "info", "warn", and "err".
    if log_level.lower() not in ('debug', 'warn', 'error', 'info', 'trace'):
        hookenv.log('invalid log level config %s' % log_level,
                    hookenv.WARNING)
        log_level = 'debug'
    # Set the extra values on the data object that will be used to write JSON.
    # https://consul.io/docs/agent/options.htm
    defaults['datacenter'] = os.environ.get('JUJU_ENV_NAME', 'dc1')
    defaults['node_name'] = hookenv.local_unit().replace('/', '-')
    defaults['domain'] = config.get('domain')
    defaults['log_level'] = log_level.lower()

    bootstrap_expect = config.get('bootstrap-expect')
    if int(bootstrap_expect) % 2 == 0:
        hookenv.log('even values for bootstrap-expect is highly discourged',
                    hookenv.WARNING)
    defaults['bootstrap_expect'] = int(bootstrap_expect)

    return defaults
