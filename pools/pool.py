from types import FunctionType
import time
import sys
import gc


class PoolTest(object):
    def __init__(self, worker_count):
        self.worker_count = worker_count
        self.pool = self.init_pool(worker_count)
        self.compute_resource = self.init_compute_resource()
        self.network_resource = self.init_network_resource()

    def init_pool(self, worker_count):
        raise NotImplementedError()

    def destroy_pool(self):
        pass

    def map(self, work_func, inputs):
        raise NotImplementedError()

    def init_compute_resource(self):
        from cmath import sqrt
        return sqrt

    def init_network_resource(self):
        import requests
        return requests

    @staticmethod
    def do_compute_work(args):
        compute_resource, num, *_ = args
        sqrt = compute_resource
        sqrt(sqrt(sqrt(num)))

    @staticmethod
    def do_network_work(args):
        network_resource, *_ = args
        requests = network_resource
        with requests.Session() as s:
            adapter = requests.adapters.HTTPAdapter(max_retries=3)
            s.mount('http://', adapter)
            s.get('http://localhost:8080/')
    
    def run_compute_test(self, jobs: int, trials: int):
        return self._run_test(self.do_compute_work, self.compute_resource, jobs, trials)

    def run_network_test(self, jobs: int, trials: int):
        return self._run_test(self.do_network_work, self.network_resource, jobs, trials)

    def _run_test(self, work_func: FunctionType, work_resource, jobs: int, trials: int):
        results = {
            'jobs': jobs,
            'trials': trials,
            'time': [],
            'blocks': [],
        }
        # Forcibly evaluate the inputs to prevent time/resources taken up later
        inputs = list(zip(
            [work_resource] * jobs,
            range(jobs)
        ))
        gc.collect()
        for _ in range(trials):
            # Run trial of pool map function and measure it
            blocks_start = sys.getallocatedblocks()
            time_start = time.time()
            list(self.map(work_func, inputs))
            time_end = time.time()
            results['time'].append(time_end - time_start)
            # Deallocate local variables we don't need anymore to give more
            # accurate metrics on memory usage
            del time_start, time_end
            gc.collect()
            blocks_end = sys.getallocatedblocks()
            results['blocks'].append(blocks_end - blocks_start if blocks_end - blocks_start > 0 else 0)
        return results

