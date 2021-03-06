from pools import PoolTest
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


class StandardProcessPool(PoolTest):
    def init_pool(self, worker_count):
        return ProcessPoolExecutor(worker_count)

    def map(self, work_func, inputs):
        return self.pool.map(work_func, inputs)


class StandardThreadPool(PoolTest):
    def init_pool(self, worker_count):
        return ThreadPoolExecutor(worker_count)

    def map(self, work_func, inputs):
        return self.pool.map(work_func, inputs)
