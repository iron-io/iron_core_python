import iron_core
import unittest
import os


class TestConfig(unittest.TestCase):
    def setUp(self):
        # Backup their ~/.iron.json file if it exists
        if os.path.exists(os.path.join(os.environ["HOME"], ".iron.json")):
            os.rename(os.path.join(os.environ["HOME"], ".iron.json"),
                    os.path.join(os.environ["HOME"], ".iron.bak.json"))

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

    def test_fromArgsMissingAPIVersion(self):
        self.assertRaises(ValueError, iron_core.IronClient, name="Test",
                version="0.1.0", product="iron_worker", token="TEST",
                host="worker-aws-us-east-1.iron.io", project_id="TEST")

    def test_fromArgsMissingHost(self):
        self.assertRaises(ValueError, iron_core.IronClient, name="Test",
                version="0.1.0", product="iron_worker", token="TEST",
                api_version=2, project_id="TEST")

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
        self.assertEqual(client.headers["Authorization"], "OAuth TEST")
        self.assertEqual(client.base_url,
                "https://worker-aws-us-east-1.iron.io:443/2/projects/TEST2/")

    def test_fromArgsUseHTTP(self):
        client = iron_core.IronClient(name="Test", version="0.1.0",
                product="iron_worker", token="TEST", project_id="TEST2",
                api_version=2, host="worker-aws-us-east-1.iron.io", port=80,
                protocol="http")
        self.assertEqual(client.port, 80)
        self.assertEqual(client.protocol, "http")


if __name__ == "__main__":
    unittest.main()
