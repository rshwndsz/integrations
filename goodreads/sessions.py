import logging
import sys
from time import sleep
import requests

from fake_useragent import UserAgent
from stem import Signal, SocketError
from stem.connection import MissingPassword, PasswordAuthFailed
from stem.control import Controller

from . import log as L
logger = L.getLogger(__name__, logging.DEBUG)


def getSession(useFakeUserAgent=True, useTor=False, rotateIp=False):
    s = requests.Session()

    if useFakeUserAgent:
        headers = {
            # https://github.com/hellysmile/fake-useragent/issues/81#issuecomment-563242847
            "User-Agent": UserAgent(use_cache_server=False, verify_ssl=False).random
        }
        s.headers.update(headers)

    if useTor:
        proxies = {
            "http": "socks5://127.0.0.1:9050",
            "https": "socks5://127.0.0.1:9050",
        }
        s.proxies = proxies

        # Connect to Tor
        # https://stem.torproject.org/_modules/stem/control.html
        try:
            controller = Controller.from_port(port=9051)
        except SocketError as e:
            logger.critical(f"Unable to connect to tor on port 9051: {e}")
            sys.exit(1)

        # Authenticate with password from ~/.torrc
        try:
            controller.authenticate()
        except (MissingPassword, PasswordAuthFailed) as e:
            logger.critical(f"Invalid Password: {e}")
            sys.exit(1)

        # Check if Tor SOCKS Proxy is working
        # https://tor.stackexchange.com/a/19859
        status = None
        for _ in range(3):
            status = controller.get_info("status/circuit-established")
            if status == "1":
                break
            logger.warning("status/circuit-established != 1. Retrying...")
            sleep(1)
        if not status:
            logger.critical("Tor circuit not established. Something is wrong.")
            sys.exit(1)

        # Get new IP from Tor
        # https://stem.torproject.org/faq.html#how-do-i-request-a-new-identity-from-tor
        if rotateIp:
            controller.signal(Signal.NEWNYM)  # type: ignore

        controller.close()

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
