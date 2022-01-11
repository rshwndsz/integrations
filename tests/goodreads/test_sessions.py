import requests
from goodreads.sessions import getSession, getIP


def test_getSession():
    s = requests.Session()
    myIP = getIP(s)
    print(myIP)

    s = getSession()
    torIP = getIP(s)
    print(torIP)

    assert myIP != torIP
