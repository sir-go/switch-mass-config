import pytest

from swlib.snmp_term import SnmpTerminal


@pytest.fixture(scope='module')
def st():
    return SnmpTerminal('172.17.0.11')


def test_term(st: SnmpTerminal):
    assert str(st) == '< snmp_terminal object ip:172.17.0.11>'


def test_get_macs(st: SnmpTerminal):
    assert sorted(st.get_macs()) == sorted({'010203040506', '0a141e28323c'})


def test_get_ifspeed_table(st: SnmpTerminal):
    assert st.get_ifspeed_table() == {
        '3.6.1.2.1.2.2.1.5.1': 1000000000,
        '3.6.1.2.1.2.2.1.5.2': 1000000000,
        '3.6.1.2.1.2.2.1.5.3': 10000000,
        '3.6.1.2.1.2.2.1.5.4': 0,
        '3.6.1.2.1.2.2.1.5.5': 0}


def test_get_location(st: SnmpTerminal):
    assert st.get_location() == 'here'


def test_get_if_indexes(st: SnmpTerminal):
    assert [vb.val for vb in st.get_if_indexes()] == [1, 2, 3, 1024, 1033]


def test_get_ports_by_types(st: SnmpTerminal):
    assert st.get_ports_by_types() == {6: [1, 2, 3], 135: [1024, 1033]}


def test_set_port_alias(st: SnmpTerminal):
    assert st.set_port_alias(6, 'pepe') is None


def test_get_serial_number(st: SnmpTerminal):
    assert st.get_serial_number() == 'R3144D7001282'


def test_get_firmware(st: SnmpTerminal):
    assert st.get_firmware() == ('4.19.R011', 'B1')


def test_get_descr(st: SnmpTerminal):
    assert st.get_descr() == 'DGS-3120-24SC Gigabit Ethernet Switch'
