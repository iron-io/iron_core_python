import httplib
import time
import os
try:
    import json
except:
    import simplejson as json


class TooManyRetriesError(Exception):
    def __str__(self):
        return repr("Max retries reached. Aborting.")


class IronClient:
    def __init__(self, name, version, product, host=None, project_id=None,
            token=None, protocol=None, port=None, api_version=None,
            config_file=None):
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
        """
        config = {
                "host": None,
                "protocol": "https",
                "port": 443,
                "api_version": None,
                "project_id": None,
                "token": None,
        }
        config = configFromFile(config,
                os.path.expanduser(".iron.json"), product)
        config = configFromEnv(config)
        config = configFromEnv(config, product)
        config = configFromFile(config, "iron.json", product)
        config = configFromFile(config, config_file, product)
        config = configFromArgs(config, host=host, project_id=project_id,
                token=token, protocol=protocol, port=port,
                api_version=api_version)

        required_fields = ["host", "api_version", "project_id", "token"]

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
        if self.protocol == "https" and self.port != httplib.HTTPS_PORT:
            raise ValueError("Invalid port (%s) for an HTTPS request. Want %s."
                    % (self.port, httplib.HTTPS_PORT))

    @classmethod
    def retry(f, exceptionToCheck, tries=5, delay=.5, backoff=2, logger=None,
            exceptionToRaise=TooManyRetriesError):
        """A decorator to implement exponential backoff in other functions.

        Keyword arguments:
        f -- The function. Automatically supplied when retry is a decorator.
             Required.
        exceptionToCheck -- The exception class that should trigger a retry.
        tries -- The maximum number of times to try. Defaults to 5.
        delay -- The initial delay (in seconds) before retrying. Defaults
                 to .5.
        backoff -- The number to multiply delay by after every failure.
                   Defaults to 2.
        logger -- an instance of logging to log debug info to. Defaults
                  to None.
        exceptionToRaise -- The exception class that should be raised after
                            tries has been reached. Defaults to
                            iron_core.TooManyRetriesError.
        """
        if backoff <= 1:
                raise ValueError("backoff must be greater than 1")

        if tries < 0:
                raise ValueError("tries must be 0 or greater")

        if delay <= 0:
                raise ValueError("delay must be greater than 0")

        def deco_retry(f):
            def f_retry(*args, **kwargs):
                # makes args modifiable
                mtries = tries
                mdelay = delay
                done = False
                rv = None
                while mtries > 0 and not done:
                    try_msg = "Attempt #%s" % (tries - mtries + 1)
                    try:
                        if logger:
                            logger.debug(try_msg)
                        rv = f(*args, **kwargs)
                        done = True
                    except exceptionToCheck, e:
                        err_s = ""
                        if "%s" % e != "":
                            err_s = " (\"%s\")" % e
                        try_s = ""
                        if mtries > 1:
                            try_s = " Retrying after %s seconds." % mdelay
                        if logger:
                            logger.debug("Failed%s.%s", err_s, try_s)
                        rv = None
                        done = False
                        if mtries > 1:
                            time.sleep(mdelay)
                            mdelay *= backoff
                        mtries -= 1
                if done:
                    if logger:
                        logger.debug("Success! Returning.")
                    return rv
                raise exceptionToRaise
            return f_retry
        return deco_retry

    def request(self, url, method, body="", headers={}):
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
        """
        if headers:
            headers = dict(list(headers.items()) + list(self.headers.items()))
        else:
            headers = self.headers

        if self.protocol == "http":
            conn = httplib.HTTPConnection(self.host, self.port)
        elif self.protocol == "https":
            conn = httplib.HTTPSConnection(self.host, self.port)
        else:
            raise ValueError("Invalid protocol.")

        url = self.base_url + url

        conn.request(method, url, body, headers)
        resp = conn.getresponse()
        result = {}
        result["body"] = resp.read()
        result["status"] = resp.status
        conn.close()
        return result

    def get(self, url, headers={}):
        """Execute an HTTP GET request and return a dict containing the
        response and the response status code.

        Keyword arguments:
        url -- The path to execute the result against, not including the API
               version or project ID, with no leading /. Required.
        headers -- HTTP Headers to send with the request. Can overwrite the
                   defaults. Defaults to {}.
        """
        return self.request(url=url, method="GET", headers=headers)

    def post(self, url, body="", headers={}):
        """Execute an HTTP POST request and return a dict containing the
        response and the response status code.

        Keyword arguments:
        url -- The path to execute the result against, not including the API
               version or project ID, with no leading /. Required.
        body -- A string or file object to send as the body of the request.
                Defaults to an empty string.
        headers -- HTTP Headers to send with the request. Can overwrite the
                   defaults. Defaults to {}.
        """
        headers["Content-Length"] = len(body)
        return self.request(url=url, method="POST", body=body, headers=headers)

    def delete(self, url, headers={}):
        """Execute an HTTP DELETE request and return a dict containing the
        response and the response status code.

        Keyword arguments:
        url -- The path to execute the result against, not including the API
               version or project ID, with no leading /. Required.
        headers -- HTTP Headers to send with the request. Can overwrite the
                   defaults. Defaults to an empty dict.
        """
        return self.request(url=url, method="DELETE", headers=headers)

    def put(self, url, body="", headers={}):
        """Execute an HTTP PUT request and return a dict containing the
        response and the response status code.

        Keyword arguments:
        url -- The path to execute the result against, not including the API
               version or project ID, with no leading /. Required.
        body -- A string or file object to send as the body of the request.
                Defaults to an empty string.
        headers -- HTTP Headers to send with the request. Can overwrite the
                defaults. Defaults to {}.
        """
        return self.request(url=url, method="PUT", body=body, headers=headers)


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
        key = "%s_%s" % (product, config[k])
        if key.upper() in os.environ:
            config[k] = os.environ[key.upper()]
    return config


def configFromArgs(config, **kwargs):
    for k in kwargs:
        if kwargs[k] is not None:
            config[k] = kwargs[k]
    return config
