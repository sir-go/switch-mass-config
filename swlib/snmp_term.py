from netsnmp import VarList, Varbind
from netsnmp import Session
from typing import Iterable


def mac_dec_to_hex(dec_bytes: Iterable[int]) -> str:
    return ''.join(map(lambda x: f'{int(x):02x}', dec_bytes))


class SnmpTerminal:
    def __init__(self,
                 ip: str,
                 w_com: str = 'private',
                 ver: int = 2,
                 timeout: int = 2,
                 retries: int = 3,
                 **args):
        self.ip = ip
        self._t = Session(
            DestHost=ip,
            Version=ver,
            Timeout=int(timeout * 1000000),
            Retries=retries,
            Community=w_com,
            **args)

    def __repr__(self):
        return '< snmp_terminal object ip:{}>'.format(self.ip)

    def get_macs(self) -> set[str]:
        res = set()
        for macaddr in self._t.walk(
                VarList(Varbind('iso.3.6.1.2.1.2.2.1.6'))):
            if not macaddr:
                continue
            mac = mac_dec_to_hex(macaddr)
            if mac == '0' * 12:
                continue
            res.add(mac)
        return res

    def get_mac_table(self) -> dict:
        res = {}
        vb_mac_table = Varbind('iso.3.6.1.2.1.17.7.1.2.2.1.2')
        vl_mac_table = VarList(vb_mac_table)
        port_numbers_values = self._t.walk(vl_mac_table)
        idx = 0
        for vb in vl_mac_table:
            port_numbers_key_split = vb.tag.split('.')[-7:]
            mac_dec = port_numbers_key_split[1:]
            mac = mac_dec_to_hex(mac_dec)
            port = port_numbers_values[idx]
            idx += 1
            if port != "0":
                if port not in res:
                    res[port] = []
                if mac and int(mac, 16) and mac not in res[port]:
                    res[port].append(mac)
        self.Retries -= 1
        if self.Retries:
            res = self.get_mac_table()
        return res

    def get_ifspeed_table(self) -> dict:
        res = {}
        vb = Varbind('iso.3.6.1.2.1.2.2.1.5')
        vl = VarList(vb)
        for vbind in self._t.walk(vl):
            res[vbind.iid] = vbind.val
        return res

    def get_location(self) -> str:
        vb = Varbind('iso.1.3.6.1.2.1.1.6.0')
        vl = VarList(vb)
        for vbind in self._t.get(vl):
            return vbind.val

    def set_location(self, location, check=False):
        self._t.set((Varbind('1.3.6.1.2.1.1.6', 0, location, 'OCTETSTR'),))
        if check:
            return self.get_location()

    def get_if_indexes(self) -> list:
        vb = Varbind('iso.3.6.1.2.1.2.2.1.1')
        vl = VarList(vb)
        return self._t.walk(vl)

    def get_ports_by_types(self) -> dict:
        if_indexes = self.get_if_indexes()
        res = {}
        vb = Varbind('iso.3.6.1.2.1.2.2.1.3')
        vl = VarList(vb)
        types = self._t.walk(vl)

        for if_type in zip(if_indexes, types):
            if if_type[1].val not in res:
                res[if_type[1].val] = []
            res[if_type[1].val].append(if_type[0].val)
        return res

    def set_port_alias(self, port_num: int, alias: str):
        self._t.set((Varbind(
            'iso.3.6.1.2.1.31.1.1.1.18', int(port_num), alias, 'OCTETSTR'),))

    def get_serial_number(self) -> str:
        vb = Varbind('iso.3.6.1.4.1.171.12.1.1.12')
        vl = VarList(vb)
        sn = self._t.walk(vl)
        if sn:
            return sn[0].val

    def get_firmware(self) -> (str, str):
        # firmware
        vb = Varbind('iso.3.6.1.2.1.16.19.2')
        vl = VarList(vb)
        fw = self._t.walk(vl)
        if fw:
            fw = fw[0].val

        # revision
        vb = Varbind('iso.3.6.1.2.1.16.19.3')
        vl = VarList(vb)
        rv = self._t.walk(vl)
        if rv:
            rv = rv[0].val
        return fw, rv

    def get_descr(self) -> str:
        vb = Varbind('.1.3.6.1.2.1.1.1.0')
        vl = VarList(vb)
        for vbind in self._t.get(vl):
            return vbind.val
