#!/usr/bin/env python

from charmhelpers.fetch import archiveurl
from path import path

# The url prefix for the consul release download files.
URL_PREFIX = 'https://dl.bintray.com/mitchellh/consul/'


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
