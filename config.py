from swlib.class_switch import Switch
from multiprocessing import Lock

conf = dict(
    scan_workers=10,            # runners amount
    root_sw_mac='',             # server MAC for uplink detection
    targets=[],                 # switches IP
    ignored_ips=[],             # ignored IP

    common_sw_params=dict(
        login='',                   # telnet username
        password='',                # telnet password
        # snmp_public='public',     # snmp read-only community
        # snmp_private='private',   # snmp write community
        # telnet_timeout=5,         # telnet waiting timeout in sec
        # snmp_timeout=5,           # snmp waiting timeout in sec
    )
)


# what to do with each device
def do(sw: Switch, lock: Lock):
    descr = sw.get_descr()
    fw = sw.get_firmware()
    with lock:
        print(descr if descr else sw.log)
        print(fw)
