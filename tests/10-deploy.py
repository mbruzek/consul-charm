#!/usr/bin/env python3

import amulet
import requests
import unittest


seconds = 1100
configuration = {
    'log-level': 'trace',
    'bootstrap-expect': 3,
    'domain': 'jujusolutions.com',
}


class TestDeployment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deployment = amulet.Deployment(series='trusty')

        cls.deployment.add('consul', units=3)
        cls.deployment.configure('consul', configuration)
        cls.deployment.expose('consul')

        try:
            cls.deployment.setup(timeout=seconds)
            cls.deployment.sentry.wait()
        except amulet.helpers.TimeoutError:
            message = "The deploy did not setup in {0} seconds".format(seconds)
            amulet.raise_status(amulet.SKIP, msg=message)
        except:
            raise

    def test_consul_binary(self):
        ''' Verify that the consul binary is installed and in the path. '''
        for unit in self.deployment.sentry['consul']:
            address = unit.info['public-address']
            print(address)
            output, code = unit.run('consul version')
            print(output)
            if code != 0:
                message = 'Consul not installed on {0}!'.format(address)
                amulet.raise_status(amulet.FAIL, msg=message)

    def test_config(self):
        ''' Verify the configuration file contains the proper values. '''
        for unit in self.deployment.sentry['consul']:
            contents = unit.file_contents('/etc/consul.json')
            if contents:
                search = configuration['domain']
                if search not in contents:
                    message = 'Config file did not contain {0}'.format(search)
                    amulet.raise_status(amulet.FAIL, msg=message)
                else:
                    print('The correct domain was in the file.')
                search = configuration['log-level']
                if search not in contents:
                    message = 'Config file did not conatain {0}'.format(search)
                    amulet.raise_status(amulet.FAIL, msg=message)
                else:
                    print('The correct log-level was in the file.')

    def test_web_ui(self):
        ''' Verify that the web ui is responding to HTTP GET requests. '''
        ui_address = self.deployment.sentry['consul'][0].info['public-address']
        ui_url = 'http://{0}:8500/ui/'.format(ui_address)
        print(ui_url)
        response = requests.get(ui_url)
        response.raise_for_status()
        consul = 'Consul'
        # Search for the product name on the main page.
        index = response.text.find(consul)
        if index != -1:
            print('Website was up and contained "{0}"!'.format(consul))
        else:
            message = 'Unable to find "{0}" in response.'.format(consul)
            print(message)
            amulet.raise_status(amulet.FAIL, msg=message)


if __name__ == '__main__':
    unittest.main()
