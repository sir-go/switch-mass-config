import pytest

from swlib.class_switch import Switch


@pytest.fixture(scope='module')
def sw():
    return Switch('172.17.0.11', 'username', 'password')


def test_repr(sw: Switch):
    assert str(sw) == 'ip: 172.17.0.11\t|descr: \t|up: None\t|p100: \t|p1000: '


def test_telnet(sw: Switch):
    assert sw.telnet_exec('ping\r') == 'pong'
