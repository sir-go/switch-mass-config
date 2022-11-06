# -*-coding:utf-8-*-
import multiprocessing
import ipaddress
from typing import Iterable, Callable


class NetScaner:
    def __init__(self):

        # input queue with host ip's
        self.q_in = multiprocessing.JoinableQueue()

    def scan(self, subnet: str = None, targets: Iterable[str] = None,
             workers_amount: int = 3, task: Callable = None):

        if subnet:
            # get subnet pool
            ipv4subnet = ipaddress.IPv4Network(subnet)

            if str(ipv4subnet.hostmask) == '0.0.0.0':
                self.q_in.put(str(subnet).split('/')[0])

            else:
                # fill input queue by ip's
                for ip_addr in ipv4subnet.hosts():
                    self.q_in.put(str(ip_addr))

        elif targets:
            for obj in targets:
                self.q_in.put(str(obj))

        # if ips' count < max_workers then workers_count = ips' count
        # else workers_count = max_workers
        num_process = self.q_in.qsize() \
            if self.q_in.qsize() < workers_amount \
            else workers_amount

        # creating processes
        lck = multiprocessing.Lock()
        for i in range(num_process):
            worker = multiprocessing.Process(
                target=task, args=(self.q_in, lck))
            worker.daemon = True
            worker.start()

        # lock input queue
        self.q_in.join()
