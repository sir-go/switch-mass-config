#!/usr/bin/env python
# -*-coding:utf-8-*-

from swlib.net_scaner import NetScaner
from swlib.class_switch import Switch
from config import *


def proc(qi, lck=None):
    while True:
        ip = qi.get()
        lck.acquire()
        print(str(qi.qsize() + 1), ip)
        lck.release()

        sw = Switch(ip, switch_auth)

        if sw.telnet_available:
            script = '''
            '''
            result = sw.telnet_exec(script, False)

            lck.acquire()
            print(sw, result)
            lck.release()
        qi.task_done()


if __name__ == '__main__':
    scn = NetScaner()
    if targets:
        scn.scan(objlist=targets, workers=scan_workers, task=proc)
