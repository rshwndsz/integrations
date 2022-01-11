import requests
from goodreads.tor import getSession, getIp


def test_getSession():
    s = requests.Session()
    myIp = getIp(s)
    print(myIp)

    s = getSession()
    torIp = getIp(s)
    print(torIp)

    assert myIp != torIp

