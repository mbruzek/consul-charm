#!/usr/bin/env python


def pre_install():
    """
    Do any setup required before the rest of the python loads.
    """
    install_charmhelpers()
    install_path()


def install_charmhelpers():
    """
    Install the charmhelpers python library, if not present.
    """
    try:
        import charmhelpers  # noqa
    except ImportError:
        import subprocess
        subprocess.check_call(['apt-get', 'install', '-y', 'python-pip'])
        subprocess.check_call(['pip', 'install', 'charmhelpers'])


def install_path():
    """
    Install the path.py python library, if not present.
    """
    try:
        import path  # noqa
    except ImportError:
        import subprocess
        subprocess.check_call(['apt-get', 'install', '-y', 'python-pip'])
        subprocess.check_call(['pip', 'install', 'path.py'])
