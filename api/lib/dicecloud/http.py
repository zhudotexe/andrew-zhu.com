import json
import logging

import requests

from .errors import Forbidden, HTTPException, NotFound, Timeout

MAX_TRIES = 10
log = logging.getLogger(__name__)


class DicecloudHTTP:
    def __init__(self, api_base, api_key, debug=False):
        self.base = api_base
        self.key = api_key
        self.debug = debug

    def request(self, method, endpoint, body, headers=None, query=None):
        if headers is None:
            headers = {}
        if query is None:
            query = {}

        if body is not None:
            if isinstance(body, str):
                headers["Content-Type"] = "text/plain"
            else:
                body = json.dumps(body)
                headers["Content-Type"] = "application/json"

        if self.debug:
            print(f"{method} {endpoint}: {body}")
        data = None
        for _ in range(MAX_TRIES):
            try:
                resp = requests.request(method, f"{self.base}{endpoint}", data=body, headers=headers, params=query)
                log.info(f"Dicecloud returned {resp.status_code} ({endpoint})")
                if resp.status_code == 200:
                    data = resp.json(encoding='utf-8')
                    break
                elif resp.status_code == 429:
                    timeout = resp.json(encoding='utf-8')
                    log.warning(f"Dicecloud ratelimit hit ({endpoint}) - resets in {timeout}ms")
                    raise Timeout("You have hit the rate limit.")
                elif 400 <= resp.status_code < 600:
                    if resp.status_code == 403:
                        raise Forbidden(resp.reason)
                    elif resp.status_code == 404:
                        raise NotFound(resp.reason)
                    else:
                        raise HTTPException(resp.status_code, resp.reason)
                else:
                    log.warning(f"Unknown response from Dicecloud: {resp.status_code}")
            except requests.ConnectionError:
                raise HTTPException(None, "Server disconnected")
        if not data:  # we did 10 loops and always got either 200 or 429 but we have no data, so we must have 429ed
            raise Timeout(f"Dicecloud failed to respond after {MAX_TRIES} tries. Please try again.")

        return data

    def get(self, endpoint):
        return self.request("GET", endpoint, None, query={"key": self.key})

    def post(self, endpoint, body):
        return self.request("POST", endpoint, body, headers={"Authorization": self.key})

    def put(self, endpoint, body):
        return self.request("PUT", endpoint, body, headers={"Authorization": self.key})

    def delete(self, endpoint):
        return self.request("DELETE", endpoint, None, headers={"Authorization": self.key})
