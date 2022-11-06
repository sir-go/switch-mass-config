from swlib.net_scaner import NetScaner
from config import conf, do
from swlib.class_switch import Switch


def proc(qi, lck=None):
    while True:
        ip = qi.get()
        do(Switch(ip, **conf['common_sw_params']), lck)
        qi.task_done()


if __name__ == '__main__':
    scn = NetScaner()
    if len(conf['targets']) < 1:
        print('no targets are set, edit the config.py please')
        exit(0)

    scn.scan(
        targets=conf['targets'],
        workers_amount=conf['scan_workers'],
        task=proc)
