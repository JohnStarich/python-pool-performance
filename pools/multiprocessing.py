from pools import PoolTest
from multiprocessing.pool import ThreadPool, Pool


class MultiprocessingProcessPool(PoolTest):
    def init_pool(self, worker_count):
        return Pool(worker_count)

    def map(self, work_func, inputs):
        return self.pool.imap_unordered(work_func, inputs)


class MultiprocessingThreadPool(PoolTest):
    def init_pool(self, worker_count):
        return ThreadPool(worker_count)

    def map(self, work_func, inputs):
        return self.pool.imap_unordered(work_func, inputs)

