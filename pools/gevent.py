from pools import PoolTest
import socket
from gevent import monkey
from gevent.pool import Pool


class GeventPool(PoolTest):
    def init_pool(self, worker_count):
        monkey.patch_socket()
        return Pool(worker_count)

    def destroy_pool(self):
        reload(socket)

    def map(self, work_func, inputs):
        return self.pool.imap_unordered(work_func, inputs)

