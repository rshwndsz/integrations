import logging
import sys
from time import sleep
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from fake_useragent import UserAgent
from stem import Signal, SocketError
from stem.connection import MissingPassword, PasswordAuthFailed
from stem.control import Controller

from integrations.common import log as L

logger = L.getLogger(
    __name__,
    localLevel="INFO",
    rootLevel="INFO",
    console=False
)


def getTorController():
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
        controller.close()
        logger.critical(f"Invalid Password: {e}")
        sys.exit(1)

    return controller


def isTorSocksProxyUp(nRetries=3, backoffTime=1):
    # https://tor.stackexchange.com/a/19859
    status = None
    controller = getTorController()

    for _ in range(nRetries):
        status = controller.get_info("status/circuit-established")
        if status == "1":
            break
        logger.warning(
            f"status/circuit-established != 1. Retrying in {backoffTime}s..."
        )
        sleep(backoffTime)

    controller.close()
    return status


def getSession(useFakeUserAgent=True, useTor=False, rotateIp=False, maxRetries=3):
    s = requests.Session()

    # https://stackoverflow.com/a/47475019
    retryStrategy = Retry(total=maxRetries)
    adapter = HTTPAdapter(max_retries=retryStrategy)
    s.mount("http://", adapter)
    s.mount("https://", adapter)

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

        controller = getTorController()

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
