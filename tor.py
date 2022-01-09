import argparse

import requests
from stem import Signal
from stem.control import Controller
from fake_useragent import UserAgent


def getSession(rotateIp=False):
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
    if rotateIp:
        with Controller.from_port(port = 9051) as c:
            c.authenticate()
            c.signal(Signal.NEWNYM) # type: ignore

    return s


def getIp(session):
    r = session.get("https://ipinfo.io/json")
    j = r.json()
    return f"IP: {j['ip']} in {j['city']}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rotateIp", dest="rotateIp", action="store_true")
    args = parser.parse_args()

    s = getSession(rotateIp=args.rotateIp)
    print(getIp(s))

