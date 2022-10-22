# -*-coding:utf-8-*-
from netsnmp import VarList, Varbind
from netsnmp import Session as snmp_Session


class SnmpException(Exception):
    def __init__(self, value):
        Exception.__init__(self)
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


class SnmpTerminal(object):
    def __init__(self, ip, w_com='private', ver=2, timeout=2, retries=3):
        self.ip = ip
        self.w_com = w_com
        self.retries = retries
        self.snmp_con = snmp_Session(
            DestHost=self.ip,
            Version=ver,
            Timeout=int(timeout * 1000000),
            Retries=retries,
            Community=self.w_com,

        )
        self._mac_dec2hex = lambda macdec: ''.join(map(lambda x: '%0.2x' % int(x), macdec))

    def __repr__(self):
        return '< snmp_terminal object ip:{}>'.format(self.ip)

    def get_macs(self):
        res = []
        for macaddr in self.snmp_con.walk(VarList(Varbind('iso.3.6.1.2.1.2.2.1.6'))):
            if macaddr:
                mac = self._mac_notnull(macaddr)
                if mac and mac not in res:
                    res.append(macaddr.encode('hex'))
        return res

    @staticmethod
    def _mac_notnull(mac):
        mac_decoded = '%012.x' % int(mac.encode('hex'), 16)
        if mac_decoded and int(mac_decoded, 16):
            return mac_decoded
        else:
            return None

    def get_mac_table(self):
        res = {}
        vb_mac_table = Varbind('iso.3.6.1.2.1.17.7.1.2.2.1.2')
        vl_mac_table = VarList(vb_mac_table)
        port_numbers_values = self.snmp_con.walk(vl_mac_table)
        idx = 0
        for varbind in vl_mac_table:
            port_numbers_key_splited = varbind.tag.split('.')[-7:]
            # vlan = port_numbers_key_splited[0]
            mac_dec = port_numbers_key_splited[1:]
            mac = '%012.x' % int(self._mac_dec2hex(mac_dec), 16)
            port = port_numbers_values[idx]
            idx += 1
            if port != "0":
                if port not in res:
                    res[port] = []
                if mac and int(mac, 16) and mac not in res[port]:
                    res[port].append(mac)
        self.retries -= 1
        if self.retries:
            res = self.get_mac_table()
        return res

    def snmp_get_ifspeed_table(self):
        res = {}
        vb = Varbind('iso.3.6.1.2.1.2.2.1.5')
        vl = VarList(vb)
        values = self.snmp_con.walk(vl)
        for vbind in vl:
            res[vbind.iid] = vbind.val
        return res

    def location_get(self):
        res = {}
        vb = Varbind('sysLocation.0')
        vl = VarList(vb)
        values = self.snmp_con.get(vl)
        for vbind in vl:
            return vbind.val

    def location_set(self, location, check=False):
        values = self.snmp_con.set((Varbind('sysLocation', 0, location, 'OCTETSTR'),))
        if check:
            return self.location_get()

    def get_if_indexes(self):
        vb = Varbind('iso.3.6.1.2.1.2.2.1.1')
        vl = VarList(vb)
        return self.snmp_con.walk(vl)

    def get_ports_by_types(self):
        if_indexes = self.get_if_indexes()
        res = {}
        vb = Varbind('iso.3.6.1.2.1.2.2.1.3')
        vl = VarList(vb)
        types = self.snmp_con.walk(vl)

        for iftp in zip(if_indexes, types):
            if iftp[1] not in res:
                res[iftp[1]] = []
            res[iftp[1]].append(iftp[0])
        return res

    def set_port_alias(self, port_num, alias):
        self.snmp_con.set((Varbind('iso.3.6.1.2.1.31.1.1.1.18', int(port_num), alias, 'OCTETSTR'),))

    def get_serial_number(self):
        vb = Varbind('iso.3.6.1.4.1.171.12.1.1.12')
        vl = VarList(vb)
        sn = self.snmp_con.walk(vl)
        if sn:
            sn = sn[0]
        return sn

    def get_firmware(self):
        # firmware
        vb = Varbind('iso.3.6.1.2.1.16.19.2')
        vl = VarList(vb)
        fw = self.snmp_con.walk(vl)
        if fw:
            fw = fw[0]

        # revision
        vb = Varbind('iso.3.6.1.2.1.16.19.3')
        vl = VarList(vb)
        rv = self.snmp_con.walk(vl)
        if rv:
            rv = rv[0]
        return fw, rv

    def get_descr(self):
        res = {}
        vb = Varbind('sysDescr.0')
        vl = VarList(vb)
        values = self.snmp_con.get(vl)
        for vbind in vl:
            return vbind.val
