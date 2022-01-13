from time import sleep
import requests
from common import sessions as S


def test_getSessionWithTor():
    s = requests.Session()
    myIP = S.getIP(s)

    s = S.getSession(useTor=True)
    torIP = S.getIP(s)

    assert myIP != torIP


def test_getSessionWithTorAndRotatedIP():
    s = S.getSession(useTor=True)
    IP1 = S.getIP(s)

    s = S.getSession(useTor=True, rotateIp=True)
    IP2 = S.getIP(s)

    assert IP1 != IP2
