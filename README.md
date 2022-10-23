## Multiple switches reconfiguring tool

`swlib` - the library implements Telnet and SNMP interfaces to switch

### Configure
```python
switch_auth = {         # switch credentials
    'login': '',        # telnet login
    'passwd': '',       # telnet password
    'snmp_public': '',  # read SNMP community
    'snmp_private': ''  # write SNMP community
}
scan_workers = 10       # parallel processes amount
root_sw_mac = ''        # server MAC for uplink detection
targets = ()            # list of switches networks (CIDRs)
ignored_ips = ()        # list of ignored IP

```
Tasks must be described in the worker function `run.proc()`

### Install & run
```bash
virtualenv venv
source ./venv/bin/activate
pip install -r requirements.txt
python run.py
```
