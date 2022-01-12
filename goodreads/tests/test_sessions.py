from time import sleep
import requests
from goodreads.sessions import getSession, getIP


def test_getSessionWithTor():
    s = requests.Session()
    myIP = getIP(s)

    s = getSession(useTor=True)
    torIP = getIP(s)

    assert myIP != torIP


def test_getSessionWithTorAndRotatedIP():
    s = getSession(useTor=True)
    IP1 = getIP(s)

    s = getSession(useTor=True, rotateIp=True)
    IP2 = getIP(s)

    assert IP1 != IP2
