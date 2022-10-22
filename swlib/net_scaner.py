# -*-coding:utf-8-*-
import multiprocessing
import ipaddress


class NetScaner:
    def __init__(self):

        # input queue with host ip's
        self.q_in = multiprocessing.JoinableQueue()

    def scan(self, subnet=None, objlist=None, workers=None, task=None):

        workers = workers or 3

        if subnet:
            # get subnet pool
            ipv4subnet = ipaddress.IPv4Network(subnet)

            if str(ipv4subnet.hostmask) == '0.0.0.0':
                self.q_in.put(str(subnet).split('/')[0])

            else:
                # fill input queue by ip's
                for ip_addr in ipv4subnet.iterhosts():
                    self.q_in.put(str(ip_addr))
        elif objlist:
            for obj in objlist:
                self.q_in.put(str(obj))

        # if ip's count < max_workers then workers_count = ip's count else workers_count = max_workers
        num_process = self.q_in.qsize() if self.q_in.qsize() < workers else workers
        # creating processess
        lck = multiprocessing.Lock()
        for i in range(num_process):
            worker = multiprocessing.Process(target=task, args=(self.q_in, lck))
            worker.daemon = True
            worker.start()

        # lock input queue
        self.q_in.join()
        # get results of workers processing
        # scan_result - tuple of returned objects
