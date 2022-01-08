import argparse
import json

import requests
from stem import Signal
from stem.control import Controller
from fake_useragent import UserAgent


def getSession(args):
    headers = {
        # https://github.com/hellysmile/fake-useragent/issues/81#issuecomment-563242847
        'User-Agent': UserAgent(use_cache_server=False, verify_ssl=False).random
    }

    proxies = {
        "http": "socks5://127.0.0.1:9050",
        "https": "socks5://127.0.0.1:9050"
    }

    s = requests.Session()
    s.proxies = proxies 
    s.headers.update(headers)

    # https://stem.torproject.org/faq.html#how-do-i-request-a-new-identity-from-tor
    if args.rotateIp:
        with Controller.from_port(port = 9051) as c:
            c.authenticate()
            c.signal(Signal.NEWNYM) # type: ignore

    return s


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rotateIp", dest="rotateIp", action="store_true")
    args = parser.parse_args()

    s = getSession(args)

    r = s.get("https://ipinfo.io/json")
    # Check request headers
    print(json.dumps(r.request.headers.__dict__, indent=4))
    # Get location information
    print(json.dumps(r.json(), indent=4))