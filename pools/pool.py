from requests.adapters import HTTPAdapter
from collections.abc import Mapping, Sequence
from types import FunctionType
from tqdm import tqdm
import time
import sys
import gc


class PoolTest(object):
    def __init__(self, worker_count: int):
        self.worker_count = worker_count
        self.pool = self.init_pool(worker_count)
        self.compute_resource = self.init_compute_resource()
        self.network_resource = self.init_network_resource()

    def init_pool(self, worker_count: int) -> object:
        raise NotImplementedError("{} does not implement init_pool"
                                  .format(self.__class__.__name__))

    def destroy_pool(self):
        pass

    def map(self, work_func: FunctionType, inputs: Sequence) -> Sequence:
        raise NotImplementedError("{} does not implement map"
                                  .format(self.__class__.__name__))

    def init_compute_resource(self) -> object:
        from cmath import sqrt
        return sqrt

    def init_network_resource(self) -> object:
        import requests
        return requests.Session

    @staticmethod
    def do_compute_work(args) -> None:
        compute_resource, num, *_ = args
        sqrt = compute_resource
        sqrt(sqrt(sqrt(num)))

    @staticmethod
    def do_network_work(args) -> None:
        network_resource, *_ = args
        Session = network_resource
        with Session() as s:
            adapter = HTTPAdapter(max_retries=3)
            s.mount('http://', adapter)
            s.get('http://localhost:8080/')

    def run_compute_test(self, jobs: int, trials: int,
                         show_progress: bool=False) -> Mapping:
        return self._run_test(self.do_compute_work, self.compute_resource,
                              jobs, trials, show_progress=show_progress)

    def run_network_test(self, jobs: int, trials: int,
                         show_progress: bool=False) -> Mapping:
        return self._run_test(self.do_network_work, self.network_resource,
                              jobs, trials, show_progress=show_progress)

    def _run_test(self, work_func: FunctionType, work_resource: object,
                  jobs: int, trials: int,
                  show_progress: bool=False) -> Mapping:
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
        trial_iter = range(trials)
        if show_progress is True and trials > 2:
            trial_iter = tqdm(trial_iter, desc='trials')
        gc.collect()
        for _ in trial_iter:
            # Run trial of pool map function and measure it
            gc.collect()
            blocks_start = sys.getallocatedblocks()
            time_start = time.time()
            list(self.map(work_func, inputs))
            time_end = time.time()
            results['time'].append(time_end - time_start)
            # Get allocated blocks before garbage collection to show peak usage
            blocks_end = sys.getallocatedblocks()
            results['blocks'].append(blocks_end - blocks_start)
        return results
