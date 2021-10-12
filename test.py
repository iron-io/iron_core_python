from __future__ import absolute_import
import iron_core
import unittest
import os
from iron_core import KeystoneTokenProvider

try:
    import json
except:
    import simplejson as json

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Backup their ~/.iron.json file if it exists
        if os.path.exists(os.path.expanduser("~/.iron.json")):
            os.rename(os.path.expanduser("~/.iron.json"),
                    os.path.expanduser("~/.iron.bak.json"))

        # Backup their ./iron.json file if it exists
        if os.path.exists("iron.json"):
            os.rename("iron.json", "iron.bak.json")

        # Backup their environment variables, if they exist
        self.env_vars = []
        for k in os.environ.keys():
            if  k[0:5] == "IRON_":
                os.environ["BAK_" + k] = v
                env_vars.append(k)
                del(os.environ[k])

    def test_fromArgsEmpty(self):
        self.assertRaises(ValueError, iron_core.IronClient, name="Test",
                version="0.1.0", product="iron_worker")

    def test_fromArgsMissingToken(self):
        self.assertRaises(ValueError, iron_core.IronClient, name="Test",
                version="0.1.0", product="iron_worker", api_version=2,
                host="worker-aws-us-east-1.iron.io", project_id="TEST")

    def test_fromArgsMissingProjectID(self):
        self.assertRaises(ValueError, iron_core.IronClient, name="Test",
                version="0.1.0", product="iron_worker", api_version=2,
                host="worker-aws-us-east-1.iron.io", token="TEST")

    def test_fromArgsProtocolPortMismatch(self):
        self.assertRaises(ValueError, iron_core.IronClient, name="Test",
                version="0.1.0", product="iron_worker", token="TEST",
                api_version=2, project_id="TEST", port=80,
                host="worker-aws-us-east-1.iron.io")

    def test_fromArgsBareMinimum(self):
        client = iron_core.IronClient(name="Test", version="0.1.0",
                product="iron_worker", token="TEST", project_id="TEST2",
                api_version=2, host="worker-aws-us-east-1.iron.io")

        self.assertEqual(client.host, "worker-aws-us-east-1.iron.io")
        self.assertEqual(client.project_id, "TEST2")
        self.assertEqual(client.token, "TEST")
        self.assertEqual(client.protocol, "https")
        self.assertEqual(client.port, 443)
        self.assertEqual(client.api_version, 2)
        self.assertEqual(client.headers["User-Agent"], "Test (version: 0.1.0)")
        self.assertEqual(client.base_url,
                "https://worker-aws-us-east-1.iron.io/2/projects/TEST2/")

    def test_fromArgsUseHTTP(self):
        client = iron_core.IronClient(name="Test", version="0.1.0",
                product="iron_worker", token="TEST", project_id="TEST2",
                api_version=2, host="worker-aws-us-east-1.iron.io", port=80,
                protocol="http")
        self.assertEqual(client.port, 80)
        self.assertEqual(client.protocol, "http")

    def test_fromArgsConfigFileGlobal(self):
        test_config = {
                "host": "test-config-host",
                "protocol": "test-config-protocol",
                "port": "test-config-port",
                "api_version": "test-config-api-version",
                "project_id": "test-config-project-id",
                "token": "test-config-token"
        }

        file = open("test_config.json", "w")
        file.write(json.dumps(test_config))
        file.close()

        client = iron_core.IronClient(name="Test", version="0.1.0",
                product="iron_worker", config_file="test_config.json")

        self.assertEqual(client.host, test_config["host"])
        self.assertEqual(client.protocol, test_config["protocol"])
        self.assertEqual(client.port, test_config["port"])
        self.assertEqual(client.api_version, test_config["api_version"])
        self.assertEqual(client.project_id, test_config["project_id"])
        self.assertEqual(client.token, test_config["token"])

        os.remove("test_config.json")

    def test_fromArgsConfigFileProduct(self):
        test_config = {
                "iron_worker": {
                    "host": "test-config-host",
                    "protocol": "test-config-protocol",
                    "port": "test-config-port",
                    "api_version": "test-config-api-version",
                    "project_id": "test-config-project-id",
                    "token": "test-config-token"
                }
        }

        file = open("test_config.json", "w")
        file.write(json.dumps(test_config))
        file.close()

        client = iron_core.IronClient(name="Test", version="0.1.0",
                product="iron_worker", config_file="test_config.json")

        self.assertEqual(client.host, test_config["iron_worker"]["host"])
        self.assertEqual(client.protocol,
                test_config["iron_worker"]["protocol"])
        self.assertEqual(client.port, test_config["iron_worker"]["port"])
        self.assertEqual(client.api_version,
                test_config["iron_worker"]["api_version"])
        self.assertEqual(client.project_id,
                test_config["iron_worker"]["project_id"])
        self.assertEqual(client.token, test_config["iron_worker"]["token"])

        os.remove("test_config.json")

    def test_fromArgsConfigFileMixed(self):
        test_config = {
                "host": "test-config-host-global",
                "protocol": "test-config-protocol-global",
                "port": "test-config-port-global",
                "project_id": "test-config-project-id-global",
                "iron_worker": {
                    "api_version": "test-config-api-version-product",
                    "project_id": "test-config-project-id-product",
                    "token": "test-config-token-product"
                }
        }

        file = open("test_config.json", "w")
        file.write(json.dumps(test_config))
        file.close()

        client = iron_core.IronClient(name="Test", version="0.1.0",
                product="iron_worker", config_file="test_config.json")

        self.assertEqual(client.host, test_config["host"])
        self.assertEqual(client.protocol, test_config["protocol"])
        self.assertEqual(client.port, test_config["port"])
        self.assertEqual(client.api_version,
                test_config["iron_worker"]["api_version"])
        self.assertEqual(client.project_id,
                test_config["iron_worker"]["project_id"])
        self.assertEqual(client.token, test_config["iron_worker"]["token"])

        os.remove("test_config.json")

    def test_fromArgsAndArgsConfigFile(self):
        test_config = {
                "host": "test-config-host",
                "protocol": "test-config-protocol",
                "port": "test-config-port",
                "api_version": "test-config-api-version",
                "project_id": "test-config-project-id",
                "token": "test-config-token"
        }

        file = open("test_config.json", "w")
        file.write(json.dumps(test_config))
        file.close()

        client = iron_core.IronClient(name="Test", version="0.1.0",
                product="iron_worker", config_file="test_config.json",
                project_id="test-project-id-args",
                token="test-token-args")

        self.assertEqual(client.host, test_config["host"])
        self.assertEqual(client.protocol, test_config["protocol"])
        self.assertEqual(client.port, test_config["port"])
        self.assertEqual(client.api_version, test_config["api_version"])
        self.assertEqual(client.project_id, "test-project-id-args")
        self.assertEqual(client.token, "test-token-args")

        os.remove("test_config.json")

    def test_requireKeystone(self):
        test_keystone_config = {
            "project_id": "test-keystone-config-project-id",
            "keystone": {
                "server": "http://localhost/",
                "tenant": "keystone-tenant",
                "username": "keystone-username",
                "password": "keystone-password"
            }
        }
        create_test_config("test_keystone_config.json", test_keystone_config)

        client = iron_core.IronClient(name="Test", version="0.1.0",
                                      product="iron_worker", config_file="test_keystone_config.json")

        self.assertTrue(client.keystone is not None)

        os.remove("test_keystone_config.json")

    def test_initKeystoneFromJson(self):
        test_keystone_config = {
            "project_id": "test-keystone-config-project-id",
            "keystone": {
                "server": "http://localhost",
                "tenant": "keystone-tenant",
                "username": "keystone-username",
                "password": "keystone-password"
            }
        }
        create_test_config("test_keystone_config.json", test_keystone_config)

        client = iron_core.IronClient(name="Test", version="0.1.0",
                                      product="iron_worker", config_file="test_keystone_config.json")

        keystone_required_keys = ["server", "tenant", "username", "password"]
        config_keystone_keys = client.keystone.keys()

        self.assertItemsEqual(config_keystone_keys, keystone_required_keys)
        self.assertEqual(client.project_id, test_keystone_config["project_id"])

        remove_test_config("test_keystone_config.json")

    def test_initKeystoneFromConstructor(self):
        client = iron_core.IronClient(name="Test", version="0.1.0",
                                      product="iron_worker",
                                      project_id="test-keystone-config-project-id",
                                      keystone={
                                          "server": "http://localhost",
                                          "tenant": "keystone-tenant",
                                          "username": "keystone-username",
                                          "password": "keystone-password"
                                      })

        keystone_required_keys = ["server", "tenant", "username", "password"]
        config_keystone_keys = client.keystone.keys()

        self.assertItemsEqual(config_keystone_keys, keystone_required_keys)

    def test_ironTokenProvider(self):
        client = iron_core.IronTokenProvider("iron-token")
        self.assertEqual(client.getToken(), "iron-token")

    def test_checkTrailingSlash(self):
        keystone_data = {
            "server": "http://localhost",
            "tenant": "keystone-tenant",
            "username": "keystone-username",
            "password": "keystone-password"
        }
        keystone = KeystoneTokenProvider(keystone_data)
        self.assertEqual("http://localhost/", keystone.server)

def create_test_config(filename, content):
    file = open(filename, "w")
    file.write(json.dumps(content))
    file.close()

def remove_test_config(filename):
    os.remove(filename)

if __name__ == "__main__":
    unittest.main()
