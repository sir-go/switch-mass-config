# -*-coding:utf-8-*-
from telnetlib import Telnet
import socket


class TelnetTerminal(object):
    def __init__(self, ip, timeout=None):
        self.ip = ip
        self.terminal = None
        self.timeout = timeout or 5
        try:
            self.terminal = Telnet(self.ip, timeout=self.timeout)
        except socket.error as e:
            pass

    def run_script(self, script, start_str='UserName:', end_str='logout', timeout=None):
        if self.terminal:
            self.terminal.read_until(start_str.encode(), timeout=timeout or self.timeout)
            self.terminal.write(script.encode())
            return self.terminal.read_until(end_str.encode(), timeout=timeout or self.timeout).decode()
