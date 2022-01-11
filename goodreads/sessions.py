import requests


def getSession(useFakeUserAgent=True, useTor=False, rotateIp=False):
    s = requests.Session()

    if useFakeUserAgent:
        from fake_useragent import UserAgent

        headers = {
            # https://github.com/hellysmile/fake-useragent/issues/81#issuecomment-563242847
            "User-Agent": UserAgent(use_cache_server=False, verify_ssl=False).random
        }
        s.headers.update(headers)

    if useTor:
        from stem import Signal
        from stem.control import Controller

        proxies = {
            "http": "socks5://127.0.0.1:9050",
            "https": "socks5://127.0.0.1:9050",
        }
        s.proxies = proxies

        if rotateIp:
            # https://stem.torproject.org/faq.html#how-do-i-request-a-new-identity-from-tor
            with Controller.from_port(port=9051) as c:
                c.authenticate()
                c.signal(Signal.NEWNYM)  # type: ignore

    return s


def getIP(session):
    r = session.get("https://ipinfo.io/json")
    j = r.json()
    return f"IP: {j['ip']} in {j['city']}"


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("--useTor", dest="useTor", action="store_true")
    parser.add_argument(
        "useFakeUserAgent", dest="useFakeUserAgent", action="store_true"
    )
    parser.add_argument("--rotateIp", dest="rotateIp", action="store_true")
    args = parser.parse_args()

    s = getSession(
        useTor=args.useTor,
        useFakeUserAgent=args.useFakeUserAgent,
        rotateIp=args.rotateIp,
    )
    print(getIP(s))
