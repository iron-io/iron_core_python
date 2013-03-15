import time
from datetime import datetime
import os
import iso8601
import requests
try:
    import json
except:
    import simplejson as json


class IronClient:
    __version__ = "1.0.2"

    def __init__(self, name, version, product, host=None, project_id=None,
            token=None, protocol=None, port=None, api_version=None,
            config_file=None, pool_connections=None, pool_maxsize=None):
        """Prepare a Client that can make HTTP calls and return it.

        Keyword arguments:
        name -- the name of the client. Required.
        version -- the version of the client. Required.
        product -- the name of the product the client will access. Required.
        host -- the default domain the client will be requesting. Defaults
                to None.
        project_id -- the project ID the client will be requesting. Can be
                      found on http://hud.iron.io. Defaults to None.
        token -- an API token found on http://hud.iron.io. Defaults to None.
        protocol -- The default protocol the client will use for its requests.
                    Defaults to None.
        port -- The default port the client will use for its requests. Defaults
                to None.
        api_version -- The version of the API the client will use for its
                       requests. Defaults to None.
        config_file -- The config file to load configuration from. Defaults to
                       None.
        pool_connections -- The initial size of the HTTP connection pool. Defaults to
                            the `requests` library default.
        pool_maxsize -- The max. size of the HTTP connection pool. Defaults to the 
                        `requests` library default.
        """
        config = {
                "host": None,
                "protocol": "https",
                "port": 443,
                "api_version": None,
                "project_id": None,
                "token": None,
        }
        products = {
                "iron_worker": {
                    "host": "worker-aws-us-east-1.iron.io",
                    "version": 2
                },
                "iron_mq": {
                    "host": "mq-aws-us-east-1.iron.io",
                    "version": 1
                },
                "iron_cache": {
                    "host": "cache-aws-us-east-1.iron.io",
                    "version": 1
                }
        }
        if product in products:
            config["host"] = products[product]["host"]
            config["api_version"] = products[product]["version"]

        config = configFromFile(config,
                os.path.expanduser("~/.iron.json"), product)
        config = configFromEnv(config)
        config = configFromEnv(config, product)
        config = configFromFile(config, "iron.json", product)
        config = configFromFile(config, config_file, product)
        config = configFromArgs(config, host=host, project_id=project_id,
                token=token, protocol=protocol, port=port,
                api_version=api_version,
                pool_connections=pool_connections, pool_maxsize=pool_maxsize,)

        required_fields = ["project_id", "token"]

        for field in required_fields:
            if config[field] is None:
                raise ValueError("No %s set. %s is a required field." % (field,
                    field))

        self.name = name
        self.version = version
        self.product = product
        self.host = config["host"]
        self.project_id = config["project_id"]
        self.token = config["token"]
        self.protocol = config["protocol"]
        self.port = config["port"]
        self.api_version = config["api_version"]
        
        pool_connections = config.get('pool_connections', requests.adapters.DEFAULT_POOLSIZE)
        pool_maxsize = config.get('pool_maxsize', requests.adapters.DEFAULT_POOLSIZE)
        adapter = requests.adapters.HTTPAdapter(pool_connections=pool_connections, pool_maxsize=pool_maxsize)
        self.conn = requests.Session()
        self.conn.mount("http://", adapter)
        self.conn.mount("https://", adapter)
        
        self.headers = {
                "Accept": "application/json",
                "User-Agent": "%s (version: %s)" % (self.name, self.version)
        }
        if self.token:
            self.headers["Authorization"] = "OAuth %s" % self.token
        self.base_url = "%s://%s:%s/%s/" % (self.protocol, self.host,
                self.port, self.api_version)
        if self.project_id:
            self.base_url += "projects/%s/" % self.project_id
        if self.protocol == "https" and self.port != 443:
            raise ValueError("Invalid port (%s) for an HTTPS request. Want %s."
                    % (self.port, 443))

    def _doRequest(self, url, method, body="", headers={}):
        if method == "GET":
            r = self.conn.get(url, headers=headers)
        elif method == "POST":
            r = self.conn.post(url, data=body, headers=headers)
        elif method == "PUT":
            r = self.conn.put(url, data=body, headers=headers)
        elif method == "DELETE":
            r = self.conn.delete(url, data=body, headers=headers)
        else:
            raise ValueError("Invalid HTTP method")
        return r

    def request(self, url, method, body="", headers={}, retry=True):
        """Execute an HTTP request and return a dict containing the response
        and the response status code.

        Keyword arguments:
        url -- The path to execute the result against, not including the API
               version or project ID, with no leading /. Required.
        method -- The HTTP method to use. Required.
        body -- A string or file object to send as the body of the request.
                Defaults to an empty string.
        headers -- HTTP Headers to send with the request. Can overwrite the
                   defaults. Defaults to {}.
        retry -- Whether exponential backoff should be employed. Defaults
                 to True.
        """
        if headers:
            headers = dict(list(headers.items()) + list(self.headers.items()))
        else:
            headers = self.headers

        headers = dict((k.encode('ascii') if isinstance(k, unicode) else k,
                        v.encode('ascii') if isinstance(v, unicode) else v)
                        for k, v in headers.items())

        url = self.base_url + url
        if isinstance(url, unicode):
            url = url.encode('ascii')

        r = self._doRequest(url, method, body, headers)

        if r.status_code == requests.codes['service_unavailable'] and retry:
            tries = 5
            delay = .5
            backoff = 2
            while r.status_code == requests.codes['service_unavailable'] and tries > 0:
                tries -= 1
                time.sleep(delay)
                delay *= backoff
                r = self._doRequest(url, method, body, headers)

        if r.status_code >= 400:
            r.raise_for_status()

        result = {}
        contentType = r.headers["Content-Type"]
        if contentType is None:
            contentType = "text/plain"
        else:
            contentType = contentType.split(";")[0]
        if contentType.lower() == "application/json":
            try:
                result["body"] = r.json()
            except:
                result["body"] = r.text
        else:
            result["body"] = r.text
        result["status"] = r.status_code
        result["resp"] = r
        result["content-type"] = contentType
        return result

    def get(self, url, headers={}, retry=True):
        """Execute an HTTP GET request and return a dict containing the
        response and the response status code.

        Keyword arguments:
        url -- The path to execute the result against, not including the API
               version or project ID, with no leading /. Required.
        headers -- HTTP Headers to send with the request. Can overwrite the
                   defaults. Defaults to {}.
        retry -- Whether exponential backoff should be employed. Defaults
                 to True.
        """
        return self.request(url=url, method="GET", headers=headers,
                retry=retry)

    def post(self, url, body="", headers={}, retry=True):
        """Execute an HTTP POST request and return a dict containing the
        response and the response status code.

        Keyword arguments:
        url -- The path to execute the result against, not including the API
               version or project ID, with no leading /. Required.
        body -- A string or file object to send as the body of the request.
                Defaults to an empty string.
        headers -- HTTP Headers to send with the request. Can overwrite the
                   defaults. Defaults to {}.
        retry -- Whether exponential backoff should be employed. Defaults
                 to True.
        """
        headers["Content-Length"] = str(len(body))
        return self.request(url=url, method="POST", body=body, headers=headers,
                retry=retry)

    def delete(self, url, headers={}, retry=True, body=""):
        """Execute an HTTP DELETE request and return a dict containing the
        response and the response status code.

        Keyword arguments:
        url -- The path to execute the result against, not including the API
               version or project ID, with no leading /. Required.
        headers -- HTTP Headers to send with the request. Can overwrite the
                   defaults. Defaults to an empty dict.
        retry -- Whether exponential backoff should be employed. Defaults
                 to True.
        body -- A string or file object to send as the body of the request.
                Defaults to an empty string.
        """
        return self.request(url=url, method="DELETE", headers=headers,
                retry=retry, body=body)

    def put(self, url, body="", headers={}, retry=True):
        """Execute an HTTP PUT request and return a dict containing the
        response and the response status code.

        Keyword arguments:
        url -- The path to execute the result against, not including the API
               version or project ID, with no leading /. Required.
        body -- A string or file object to send as the body of the request.
                Defaults to an empty string.
        headers -- HTTP Headers to send with the request. Can overwrite the
                defaults. Defaults to {}.
        retry -- Whether exponential backoff should be employed. Defaults
                 to True.
        """
        return self.request(url=url, method="PUT", body=body, headers=headers,
                retry=retry)


    @staticmethod
    def fromRfc3339(timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()
            return timestamp
        return iso8601.parse_date(timestamp)

    @staticmethod
    def toRfc3339(timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()
        return timestamp.isoformat()

    @staticmethod
    def fromTimestamp(timestamp=None):
        if timestamp is None:
            timestamp = time.now()
            return timestamp
        return datetime.fromtimestamp(float(timestamp))

def configFromFile(config, path, product=None):
    if path is None:
        return config
    if not os.path.exists(path):
        return config
    try:
        file = open(path, "r")
    except IOError, e:
        return config
    raw = json.loads(file.read())
    for k in raw.keys():
        if k in config:
            config[k] = raw[k]
    if product is not None:
        if product in raw:
            for k in raw[product].keys():
                config[k] = raw[product][k]
    return config


def configFromEnv(config, product=None):
    if product is None:
        product = "iron"
    for k in config.keys():
        key = "%s_%s" % (product, k)
        if key.upper() in os.environ:
            config[k] = os.environ[key.upper()]
    return config


def configFromArgs(config, **kwargs):
    for k in kwargs:
        if kwargs[k] is not None:
            config[k] = kwargs[k]
    return config
