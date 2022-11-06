[![Tests](https://github.com/sir-go/switch-mass-config/actions/workflows/python-app.yml/badge.svg)](https://github.com/sir-go/switch-mass-config/actions/workflows/python-app.yml)

# Multiple switches reconfiguring tool
A tool for reconfiguring multiple d-link switches at the same time.

`swlib` - the library implements Telnet and SNMP connection interfaces to switch

## Configure
Edit the `config.py` file before run

```python
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
    with lock:
        print(descr if descr else sw.log)
```

All per-device configuration logic must be described in 
the worker function `do(sw, lock)`

## Install -> Tests -> Run
### Standalone
> The system must have the `net-snmp` package

```bash
virtualenv venv
source ./venv/bin/activate
pip install -r requirements.txt
python -m pytest && python run.py
```

### Docker
> the docker bridge network must be different from that where devices are

```bash
docker build . -t sw-mass-cfg
docker run --rm -it -v ${PWD}/config.py:/app/config.py:ro sw-mass-cfg
```
