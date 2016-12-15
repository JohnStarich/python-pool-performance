from pools import PoolTest
import eventlet


class EventletPool(PoolTest):
    def init_pool(self, worker_count):
        return eventlet.GreenPool(worker_count)

    def map(self, work_func, inputs):
        return self.pool.imap(work_func, inputs)

    def init_network_resource(self):
        return eventlet.import_patched('requests')

