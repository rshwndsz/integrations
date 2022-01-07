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
    with Controller.from_port(port = 9051) as c:
        c.authenticate()
        if args.rotateIp:
            c.signal(Signal.NEWNYM) # type: ignore

    return s


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rotateIp", dest="rotateIp", action="store_true")
    args = parser.parse_args()

    s = getSession(args)

    # Get location information
    r = s.get("https://ipinfo.io/json")
    print(json.dumps(r.request.headers.__dict__, indent=4))
    print(json.dumps(s.get('https://ipinfo.io/json').json(), indent=4))
