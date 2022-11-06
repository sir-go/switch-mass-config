import pytest
from netsnmp.client import VarList, Varbind


class FakeSNMP:
    def __init__(self):
        self.b = b''

    def walk(self, vl: VarList):
        iid = vl[0].iid
        if iid == '3.6.1.2.1.2.2.1.6':
            return [
                (1, 2, 3, 4, 5, 6),
                (1, 2, 3, 4, 5, 6),
                (10, 20, 30, 40, 50, 60)]
        if iid == '3.6.1.2.1.2.2.1.5':
            return VarList(
                Varbind('iso.3.6.1.2.1.2.2.1.5.1', val=1000000000),
                Varbind('iso.3.6.1.2.1.2.2.1.5.2', val=1000000000),
                Varbind('iso.3.6.1.2.1.2.2.1.5.3', val=10000000),
                Varbind('iso.3.6.1.2.1.2.2.1.5.4', val=0),
                Varbind('iso.3.6.1.2.1.2.2.1.5.5', val=0)
            )
        if iid == '1.3.6.1.2.1.1.6.0':
            return VarList(Varbind('iso.1.3.6.1.2.1.1.6.0', val='here'))
        if iid == '3.6.1.2.1.2.2.1.1':
            return VarList(
                Varbind('iso.3.6.1.2.1.2.2.1.1.1', val=1),
                Varbind('iso.3.6.1.2.1.2.2.1.1.2', val=2),
                Varbind('iso.3.6.1.2.1.2.2.1.1.3', val=3),
                Varbind('iso.3.6.1.2.1.2.2.1.1.1024', val=1024),
                Varbind('iso.3.6.1.2.1.2.2.1.1.1033', val=1033)
            )
        if iid == '3.6.1.2.1.2.2.1.3':
            return VarList(
                Varbind('iso.3.6.1.2.1.2.2.1.3.1', val=6),
                Varbind('iso.3.6.1.2.1.2.2.1.3.2', val=6),
                Varbind('iso.3.6.1.2.1.2.2.1.3.3', val=6),
                Varbind('iso.3.6.1.2.1.2.2.1.3.1024', val=135),
                Varbind('iso.3.6.1.2.1.2.2.1.3.1033', val=135)
            )
        if iid == '3.6.1.4.1.171.12.1.1.12':
            return VarList(
                Varbind('iso.3.6.1.4.1.171.12.1.1.12', val='R3144D7001282'),
            )
        if iid == '3.6.1.2.1.16.19.2':
            return VarList(
                Varbind('iso.3.6.1.2.1.16.19.2', val='4.19.R011'),
            )
        if iid == '3.6.1.2.1.16.19.3':
            return VarList(
                Varbind('iso.3.6.1.2.1.16.19.3', val='B1'),
            )
        if vl[0].tag == '.1.3.6.1.2.1.1.1.0':
            return VarList(
                Varbind(tag='.1.3.6.1.2.1.1.1.0',
                        val='DGS-3120-24SC Gigabit Ethernet Switch'),
            )

    def set(self, vl: VarList):
        pass


@pytest.fixture(autouse=True)
def fake_snmp(monkeypatch):
    fs = FakeSNMP()
    monkeypatch.setattr('netsnmp.client.Session.walk', fs.walk)
    monkeypatch.setattr('netsnmp.client.Session.get', fs.walk)
    monkeypatch.setattr('netsnmp.client.Session.set', fs.set)


class FakeTelnet:
    def __init__(self):
        self.b = b''

    def write(self, buff):
        self.b = buff

    def read_until(self, match, *args, **kwargs):
        if b'ping\r' in self.b:
            return b'pong'
        return b''

    def non(self, *args, **kwargs):
        pass


@pytest.fixture(autouse=True)
def fake_telnet(monkeypatch):
    ft = FakeTelnet()
    monkeypatch.setattr('telnetlib.Telnet.write', ft.write)
    monkeypatch.setattr('telnetlib.Telnet.open', ft.non)
    monkeypatch.setattr('telnetlib.Telnet.read_until', ft.read_until)
