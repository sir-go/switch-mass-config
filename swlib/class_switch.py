import re
import socket
from typing import List
from telnetlib import Telnet
from .snmp_term import SnmpTerminal


def c_join(joined_list: list[str]) -> str:
    return ', '.join(joined_list)


def list_pack(lst: List[int]) -> str:
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
    def __init__(self,
                 ip: str,
                 login: str,
                 password: str,
                 snmp_public: str = 'public',
                 snmp_private: str = 'private',
                 telnet_timeout: int = 5,
                 snmp_timeout: int = 5,
                 ):
        self.ip = ip
        self.telnet_timeout = telnet_timeout
        self.login = login
        self.password = password
        self.snmp_public = snmp_public
        self.snmp_private = snmp_private
        self.snmp_timeout = snmp_timeout
        self.log = []

        try:
            self.snmp = SnmpTerminal(ip, snmp_private, timeout=snmp_timeout)
        except (socket.error, IOError) as e:
            self.log.append(e)
            self.snmp = None

        self.uplink_port = None
        self.ports_100 = []
        self.ports_1000 = []

    def __repr__(self):
        return 'ip: {ip}\t|descr: {descr}\t|up: {uplink}\t' \
               '|p100: {p100}\t|p1000: {p1000}'.format(
                ip=self.ip,
                descr=self.get_descr(),
                uplink=self.uplink_port,
                p100=list_pack(self.ports_100),
                p1000=list_pack(self.ports_1000))

    def _run_script(self, script: str,
                    start_str: str = 'UserName:',
                    end_str: str = 'logout') -> str:
        try:
            _t = Telnet(self.ip, timeout=self.telnet_timeout)
            _t.read_until(start_str.encode())
            _t.write(script.encode())
            return _t.read_until(end_str.encode()).decode()
        except socket.error as e:
            self.log.append(e)
            return ''

    def telnet_exec(self, script: str, save_all: bool = False):
        save_all_part = "save\r" if save_all else ""
        return self._run_script(
            f"{self.login}\r"
            f"{self.password}\r"
            f"{script}"
            f"{save_all_part}"
            f"logout\r"
        )

    def save_all(self):
        self.telnet_exec("", True)

    def get_descr(self) -> str:
        descr = ''
        null_script_result = self.telnet_exec("")
        try:
            descr = null_script_result.split('\r')[-1].split(':')[0]
        finally:
            return descr

    def snmp_enable(self, save_all: bool = False):
        if self.snmp is not None:
            return
        if self.telnet_exec("enable snmp\r", save_all):
            self.snmp = SnmpTerminal(self.ip,
                                     self.snmp_private,
                                     timeout=self.snmp_timeout)

    def snmp_change_community(self, new_r: str, new_w: str):
        self.telnet_exec(
            f'delete snmp community {self.snmp_public}\r'
            f'delete snmp community {self.snmp_private}\r'
            f'create snmp community {new_w} view CommunityView read_write\r'
            f'create snmp community {new_r} view CommunityView read_only\r'
        )

    def vlan_create(self, vlan_name: str, vlan_num: int):
        return self.telnet_exec(
            f"create vlan {vlan_name} tag {vlan_num}\r"
        )

    def vlan_conf(self, vlan_name: str, vlan_tagged: bool,
                  ports: list[str] | str):
        return self.telnet_exec(
            "config vlan {vlan_name} add {tagged} {ports}\r".format(
                vlan_name=vlan_name,
                tagged='tagged' if vlan_tagged else 'untagged',
                ports='all' if ports == 'all' else ', '.join(ports)
            )
        )

    def vlan_del(self, vlan_name: str, ports: list[str]):
        return self.telnet_exec(
            "config vlan {vlan_name} delete {ports}\r".format(
                vlan_name=vlan_name,
                ports=','.join(ports)
            )
        )

    def vlan_destroy(self, vlan_name: str):
        return self.telnet_exec(f"delete vlan {vlan_name}\r")

    def vlan_set_service(self, vlan_name: str):
        return self.telnet_exec(f"config ipif System vlan {vlan_name}\r")

    def get_if_indexes(self) -> str:
        return list_pack(
            [idx for idx in self.snmp.get_if_indexes() if int(idx) < 1024])

    def get_uplink_port(self, root_device_mac: str):
        ports_macs = self.snmp.get_mac_table()
        for port, macs in ports_macs.items():
            if root_device_mac in macs:
                self.uplink_port = int(port)
                return self.uplink_port
        return self.uplink_port

    def conf_traffic_seg(self,
                         from_port: str = 'all',
                         to_port: str = 'all',
                         save_all: bool = True):
        if from_port == 'all':
            from_port = self.get_if_indexes()
        if to_port == 'all':
            to_port = self.get_if_indexes()
        return self.telnet_exec(
            f"config traffic_segmentation {from_port} "
            f"forward_list {to_port}\r", save_all
        )

    def ipif_create(self, ifname: str, ip: str, enabled: bool = True):
        return self.telnet_exec(
            "create ipif {ifname} {ip} tmp state {state}\r".format(
                ifname=ifname,
                ip=ip,
                state='enable' if enabled else 'disable'
            )
        )

    def ipif_delete(self, ifname: str):
        return self.telnet_exec(f"delete ipif {ifname}\r")

    def netbios_disable(self):
        script = "" \
                 "config filter netbios all state enable\r" \
                 "config filter extensive_netbios all state enable\r"
        return self.telnet_exec(script)

    def sntp_enable(self, sntp_srv_ip: str):
        script = f"config sntp primary {sntp_srv_ip}\r" \
                 f"enable sntp\r" \
                 f"config time_zone operator + hour 4 min 0\r"
        return self.telnet_exec(script)

    def dos_prevention_enable(self):
        return self.telnet_exec(
            "config dos_prevention dos_type all state enable\r")

    def loopdetect_enable(self, ports: list[str]):
        return self.telnet_exec("config loopdetect ports {ports} state "
                                "enable recover_timer 1800\renable "
                                "loopdetect\r".format(ports=', '.join(ports)))

    def loopdetect_disable(self, ports: list[str]):
        return self.telnet_exec(
            f"config loopdetect ports {c_join(ports)} state disable\r")

    def bpdu_protection_enable(self, ports: list[str]):
        return self.telnet_exec(
            f"config bpdu_protection ports {c_join(ports)} state enable\r"
            f"enable bpdu_protection\r"
        )

    def bpdu_protection_disable(self):
        return self.telnet_exec("disable bpdu_protection\r")

    def port_security(self, ports: list[str]):
        return self.telnet_exec(
            f"config traffic control {c_join(ports)} broadcast "
            f"enable multicast enable action shutdown "
            f"threshold 100 countdown 5 time_interval 5 \r"
            f"config traffic control {c_join(ports)} unicast disable \r"
            f"config traffic control auto_recover_time 5 \r"
            f"config port_security ports {c_join(ports)} admin_state enable "
            f"max_learning_addr 1 lock_address_mode deleteontimeout \r")

    def set_syslog_lvl_debug(self):
        return self.telnet_exec("config syslog host all severity debug\r")

    def disable_traffic_control(self):
        return self.telnet_exec(
            "config traffic control all broadcast disable "
            "multicast disable unicast disable\r")

    def disable_port_security(self):
        return self.telnet_exec(
            "config port_security ports all admin_state disable\r")

    def set_safeguard_limits(self, top: int, bottom: int):
        return self.telnet_exec(
            f"config safeguard_engine utilization "
            f"rising {top} falling {bottom}\r")

    def set_safeguard_state(self, state: bool):
        return self.telnet_exec(
            "config safeguard_engine state {0}\r".format(
                'enable' if state else 'disable')
        )

    def get_ports_by_vlan_name(self, vlan_name: str):
        txt = self.telnet_exec(f"show vlan {vlan_name}\r", False)
        re_t = r'current\s+tagged\s+ports.*:\s+(?P<ports>[\d\s,:-]+)\s+\n'
        re_u = r'current\s+untagged\s+ports.*:\s+(?P<ports>[\d\s,:-]+)\s+\n'

        def get_ports(tagged: bool = False):
            rxp = re.compile(re_t if tagged else re_u, re.I)
            reg_res = rxp.search(txt)
            return None if reg_res is None \
                else reg_res.group('ports').strip(' ')

        return {'tagged': get_ports(True), 'untagged': get_ports(False)}

    def port_security_trap_log_enable(self):
        return self.telnet_exec("enable port_security trap_log\r")

    def vlan_adv_enable(self, vlan_num: int):
        return self.telnet_exec(
            f"config vlan vlanid {vlan_num} advertisement enable\r")

    def pppoe_circuit_id(self, ports: list[str]):
        return self.telnet_exec(
            f"config pppoe circuit_id_insertion ports {c_join(ports)} "
            f"state enable circuit_id ip\r"
            f"config pppoe circuit_id_insertion state enable\r")

    def pppoe_circuit_id_disable_on_ports(self, ports: list[str]):
        return self.telnet_exec(
            f"config pppoe circuit_id_insertion "
            f"ports {c_join(ports)} state disable circuit_id ip\r")

    def pppoe_circuit_id_disable(self):
        return self.telnet_exec(
            "config pppoe circuit_id_insertion state disable\r")

    def ipif_set(self, ifname: str = 'System', ip: str = None):
        mode = 'dhcp' if ip is None or ip == 'dhcp' else f'ipaddress {ip}'
        return self.telnet_exec(f"config ipif {ifname} {mode}\r")

    def get_info(self, show_all: str = False):
        return self.telnet_exec(
            "show switch\r{0}\r".format('a' if show_all else 'q'))

    def get_firmware(self):
        info = {'fw': '', 'rev': ''}
        info_lines = self.get_info().split('\r')
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

    def accounts_get(self):
        return self.telnet_exec("show account\r")

    def account_add(self, login: str, password: str, save: bool = False):
        return self.telnet_exec(
            f"create account admin {login}\r{password}\r{password}\r", save
        )

    def account_del(self, login):
        return self.telnet_exec(f"delete account {login}\r")
