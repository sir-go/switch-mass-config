# -*-coding:utf-8-*-
import re

from .telnet_term import TelnetTerminal
from .snmp_term import SnmpTerminal


def list_pack(lst):
    """
    1,2,3,4,5,6,7,8,9,10,11,12     ->  1-12
    1,2,3,    6,7,8,9,10,11        ->  1-3,6,7-11
    1,    4,5,6,7                  ->  1,4-7
    1,2,3,  5,6,7                  ->  1-3,5-7
    1,2,3,    6,7,    10,11,12     ->  1-3,6,7,10-12
    """
    lst_prepared = [p for p in set(map(int, lst))]
    prev_number = lst_prepared[0] if lst_prepared else None
    result = []

    for number in lst_prepared:
        if number != prev_number + 1:
            result.append([number])
        elif len(result[-1]) > 1:
            result[-1][-1] = number
        else:
            result[-1].append(number)
        prev_number = number

    return ','.join(['-'.join(map(str, i)) for i in result])


class Switch:
    def __init__(self, ip, options=None):
        self.ip = ip
        self.descr = None
        self.options = options
        self.telnet = None
        self.telnet_available = None
        self.snmp = None
        self.snmp_available = None
        self.uplink_port = None
        self.ports_100 = []
        self.ports_1000 = []
        self.get_descr()

    def __repr__(self):
        return 'ip: {ip}\t|dscr: {descr}\t|up: {uplink}\t|p100: {p100}\t|p1000: {p1000}'.format(
            ip=self.ip,
            descr=self.descr,
            uplink=self.uplink_port,
            p100=list_pack(self.ports_100) if self.ports_100 else 'None',
            p1000=list_pack(self.ports_1000) if self.ports_1000 else 'None'
        )

    def telnet_connect(self):
        timeout = 5
        if 'telnet_timeout' in self.options:
            timeout = self.options
        self.telnet = TelnetTerminal(self.ip, timeout)
        self.telnet_available = self.telnet.terminal is not None
        return self.telnet_available

    def telnet_exec(self, script, save_all=True):
        if self.telnet_connect():
            script_ = "" \
                      "{login}\r" \
                      "{passwd}\r".format(**self.options)
            script_ += script
            if save_all:
                script_ += "save\r"
            script_ += "logout\r"
            return self.telnet.run_script(script_)
            # return False

    def save_all(self):
        try:
            self.telnet_exec("")
        except EOFError:
            self.telnet_available = False

    def get_descr(self):
        try:
            null_script_result = self.telnet_exec("", False)
        except EOFError:
            self.telnet_available = False
        else:
            self.descr = null_script_result.split('\r')[-1].split(':')[0]
        finally:
            return self.descr

    def snmp_enable(self, save_all=False):
        if self.telnet_exec("enable snmp\r", save_all):
            self.snmp = SnmpTerminal(self.ip, self.options['snmp_private'])

    def snmp_change_community(self, new_r=None, new_w=None, old_r=None, old_w=None):
        script = "" \
                 "delete snmp community {old_r}\r" \
                 "delete snmp community {old_w}\r" \
                 "create snmp community {new_w} view CommunityView read_write\r" \
                 "create snmp community {new_r} view CommunityView read_only\r".format(
            old_r=old_r or 'public',
            old_w=old_w or 'private',
            new_r=new_r or self.options['snmp_public'],
            new_w=new_w or self.options['snmp_private'])
        return self.telnet_exec(script)

    def snmp_get_mac_table(self):
        if self.snmp is None:
            self.snmp_enable()
        return self.snmp.get_mac_table()

    def snmp_get_ifspeed_table(self):
        if self.snmp is None:
            self.snmp_enable()
        return self.snmp.snmp_get_ifspeed_table()

    def snmp_get_firmware(self):
        if self.snmp is None:
            self.snmp_enable()
        return self.snmp.get_firmware()

    def vlan_create(self, vlan_name, vlan_num):
        return self.telnet_exec(
            "create vlan {vlan_name} tag {vlan_num}\r".format(
                vlan_name=vlan_name,
                vlan_num=vlan_num
            )
        )

    def vlan_conf(self, vlan_name, vlan_tagged, ports):
        return self.telnet_exec(
            "config vlan {vlan_name} add {tagged} {ports}\r".format(
                vlan_name=vlan_name,
                tagged='tagged' if vlan_tagged else 'untagged',
                ports='all' if ports == 'all' else ', '.join(ports)
            )
        )

    def vlan_del(self, vlan_name, ports):
        return self.telnet_exec(
            "config vlan {vlan_name} delete {ports}\r".format(
                vlan_name=vlan_name,
                ports=','.join(ports)
            )
        )

    def vlan_destroy(self, vlan_name):
        return self.telnet_exec(
            "delete vlan {vlan_name}\r".format(
                vlan_name=vlan_name
            )
        )

    def vlan_set_service(self, vlan_name):
        return self.telnet_exec(
            "config ipif System vlan {vlan_name}\r".format(
                vlan_name=vlan_name
            )
        )

    def get_if_indexes(self):
        return list_pack([idx for idx in self.snmp.get_if_indexes() if int(idx) < 1024])

    def get_uplink_port(self, root_device_mac):
        ports_macs = self.snmp_get_mac_table()
        for port, macs in ports_macs.iteritems():
            if root_device_mac in macs:
                self.uplink_port = int(port)
        return self.uplink_port

    def set_port_alias(self, port_num, alias):
        self.snmp.set_port_alias(port_num, alias)

    def conf_traffic_seg(self, from_port='all', to_port='all', save_all=True):
        if from_port == 'all':
            from_port = self.get_if_indexes()
        if to_port == 'all':
            to_port = self.get_if_indexes()
        return self.telnet_exec(
            "config traffic_segmentation {from_p} forward_list {to_p}\r".format(
                from_p=from_port,
                to_p=to_port
            ), save_all
        )

    def ipif_create(self, ifname, ip, vlan=None, enabled=True):
        return self.telnet_exec(
            "create ipif {ifname} {ip} tmp state {state}\r".format(
                ifname=ifname,
                ip=ip,
                state='enable' if enabled else 'disable'
            )
        )

    def ipif_delete(self, ifname):
        return self.telnet_exec("delete ipif {0}\r".format(ifname))

    def netbios_disable(self):
        script = "" \
                 "config filter netbios all state enable\r" \
                 "config filter extensive_netbios all state enable\r"
        return self.telnet_exec(script)

    def sntp_enable(self, sntp_srv_ip):
        script = "" \
                 "config sntp primary {sntp_srv_ip}\r" \
                 "enable sntp\r" \
                 "config time_zone operator + hour 4 min 0\r".format(sntp_srv_ip=sntp_srv_ip)
        return self.telnet_exec(script)

    def dos_prevention_enable(self):
        return self.telnet_exec("config dos_prevention dos_type all state enable\r")

    def get_ports_by_types(self):
        return self.snmp.get_ports_by_types()

    def loopdetect_enable(self, ports):
        return self.telnet_exec(
            "config loopdetect ports {ports} state enable recover_timer 1800\r" \
            "enable loopdetect\r".format(
                ports=', '.join(ports)
            )
        )

    def loopdetect_disable(self, ports):
        return self.telnet_exec("config loopdetect ports {ports} state disable\r".format(ports=', '.join(ports)))

    def bpdu_protection_enable(self, ports):
        return self.telnet_exec(
            "config bpdu_protection ports {ports} state enable\r" \
            "enable bpdu_protection\r".format(
                ports=', '.join(ports)
            )
        )

    def bpdu_protection_disable(self):
        return self.telnet_exec(
            "disable bpdu_protection\r"
        )

    def port_security(self, ports):
        return self.telnet_exec(
            "config traffic control {ports} broadcast enable multicast enable action shutdown threshold 100 countdown 5 time_interval 5 \r" \
            "config traffic control {ports} unicast disable \r" \
            "config traffic control auto_recover_time 5 \r" \
            "config port_security ports {ports} admin_state enable max_learning_addr 1 lock_address_mode deleteontimeout \r".format(
                ports=', '.join(ports)
            )
        )

    def set_syslog_lvl_debug(self):
        return self.telnet_exec(
            "config syslog host all severity debug\r"
        )

    def disable_traffic_control(self):
        return self.telnet_exec(
            "config traffic control all broadcast disable multicast disable unicast disable\r"
        )

    def disable_port_security(self):
        return self.telnet_exec(
            "config port_security ports all admin_state disable\r"
        )

    def set_safeguard_limits(self, top, bottom):
        return self.telnet_exec(
            "config safeguard_engine utilization rising {0} falling {1}\r".format(top, bottom)
        )

    def set_safeguard_state(self, state):
        return self.telnet_exec(
            "config safeguard_engine state {0}\r".format('enable' if state else 'disable')
        )

    def get_ports_by_vlan_name(self, vlan_name):
        txt = self.telnet_exec(
            "show vlan {0}\r".format(vlan_name),
            False
        )

        def get_prots(tagged=False):
            regex = re.compile(r'current\s+{0}\s+ports.*:\s+(?P<ports>[\d\s,:-]+)\s+\n'.format(
                'tagged' if tagged else 'untagged'
            ), re.I)
            reg_res = regex.search(txt)

            return None if reg_res is None else reg_res.group('ports').strip(' ')

        return {'tagged': get_prots(True), 'untagged': get_prots(False)}

    def port_security_trap_log_enable(self):
        return self.telnet_exec(
            "enable port_security trap_log\r"
        )

    def vlan_adv_enable(self, vlan_num):
        return self.telnet_exec("config vlan vlanid {0} advertisement enable\r".format(vlan_num))

    def pppoe_circuit_id(self, ports):
        return self.telnet_exec(
            "config pppoe circuit_id_insertion ports {ports} state enable circuit_id ip\r" \
            "config pppoe circuit_id_insertion state enable\r".format(
                ports=', '.join(ports)
            )
        )

    def pppoe_circuit_id_disable_on_ports(self, ports):
        return self.telnet_exec(
            "config pppoe circuit_id_insertion ports {ports} state disable circuit_id ip\r".format(
                ports=', '.join(ports)
            )
        )

    def pppoe_circuit_id_disable(self):
        return self.telnet_exec(
            "config pppoe circuit_id_insertion state disable\r"
        )

    def ipif_set(self, ifname=None, ip=None):
        if ifname is None:
            ifname = 'System'
        return self.telnet_exec(
            "config ipif {ifname} {mode}\r".format(
                ifname=ifname,
                mode='dhcp' if ip is None or ip == 'dhcp' else 'ipaddress {0}'.format(ip)
            )
        )

    def get_info(self, show_all=False):
        """
        Device Type                : DES-3200-52 Fast Ethernet Switch
        MAC Address                : AC-F1-DF-BD-49-B0
        IP Address                 : 172.16.235.195 (DHCP)
        VLAN Name                  : service
        Subnet Mask                : 255.255.0.0
        Default Gateway            : 172.16.0.1
        Boot PROM Version          : Build 4.00.001
        Firmware Version           : Build 4.00.020
        Hardware Version           : C1
        Serial Number              : R3931CC000639
        System Name                :
        System Location            :
        System Uptime              : 0 days, 1 hours, 6 minutes, 27 seconds
        """
        return self.telnet_exec("show switch\r{0}\r".format('a' if show_all else 'q'), False)

    def get_firmware(self):
        info = {'fw': '', 'rev': ''}
        info_lines = self.get_info().decode().split('\r')
        for info_line in info_lines:
            line_parts = info_line.split(':')
            if len(line_parts) > 1:
                k, v = line_parts
                k = k.lower().strip('\n')
                v = v.strip('\n')
                if k.startswith('firmware'):
                    info['fw'] = v
                elif k.startswith('hardware'):
                    info['rev'] = v
        return info

    def snmp_get_serial_number(self):
        if self.snmp is None:
            self.snmp_enable()
        return self.snmp.get_serial_number()

    def accouns_get(self):
        return self.telnet_exec("show account\r", False)

    def account_add(self, login, password, save=False):
        return self.telnet_exec(
            "create account admin {user}\r{password}\r{password}\r".format(
                user=login,
                password=password
            ), save
        )

    def account_del(self, login):
        return self.telnet_exec(
            "delete account {user}\r".format(
                user=login
            )
        )
