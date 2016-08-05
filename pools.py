#!/usr/bin/env python3

from __future__ import print_function
from multiprocessing.pool import ThreadPool, Pool
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
from eventlet import GreenPool as EventletGreenPool
from gevent.pool import Pool as GEventPool
from types import FunctionType
from tabulate import tabulate
from typing import Sequence
from numpy import cumsum
from cmath import sqrt
from tqdm import tqdm
import textwrap
import requests
import sys
import gc

import utils


def test_pool_func(
        pool_func: FunctionType,
        work_func: FunctionType,
        job_counts: Sequence[int],
        processes: int=None,
        threads: int=None):
    time_results = []
    leaked_blocks = []
    # memory_percent = []
    job_count_column = []
    for jobs in job_counts:
        job_count_column.append(jobs)
        gc.collect()
        # memory_percent_start = utils.memory_percent()
        blocks = sys.getallocatedblocks()
        time_results.append(
            pool_func(
                work_func=work_func,
                jobs=jobs,
                processes=processes,
                threads=threads,
            )
        )
        gc.collect()
        new_blocks = sys.getallocatedblocks()
        # memory_percent.append(utils.memory_percent() - memory_percent_start)
        leaked_blocks.append(new_blocks - blocks)
    return {
        "leaked blocks": leaked_blocks,
        # "leaked memory": memory_percent,
        "time": time_results,
        "jobs": job_count_column,
        # "parallel jobs": [concurrent_jobs] * len(time_results),
    }


def do_network_work(num: float):
    with requests.Session() as s:
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        s.mount('http://', adapter)
        s.get('http://localhost:8080/')


def do_compute_work(num: float):
    return sqrt(sqrt(sqrt(num)))


@utils.time_it
def do_map(map_func: FunctionType, work_func: FunctionType, jobs: int):
    list(map_func(work_func, range(int(jobs))))


def multiprocessing_process_pool(work_func: FunctionType, jobs: Sequence[int],
                                 processes: int=None, *args, **kwargs):
    pool = Pool(processes)
    time_result = do_map(pool.map, work_func, jobs)
    pool.close()
    return time_result


def multiprocessing_thread_pool(work_func: FunctionType, jobs: Sequence[int],
                                threads: int=None, *args, **kwargs):
    """Performs jobs^2 work using multiprocessing.pool.ThreadPool"""
    pool = ThreadPool(threads)
    time_result = do_map(pool.map, work_func, jobs)
    pool.close()
    return time_result


def eventlet_green_pool(work_func: FunctionType, jobs: Sequence[int],
                        threads: int=None, *args, **kwargs):
    pool = EventletGreenPool(threads)
    time_result = do_map(pool.imap, work_func, jobs)
    pool.resize(0)
    return time_result


def gevent_green_pool(work_func: FunctionType, jobs: Sequence[int],
                      threads: int=None, *args, **kwargs):
    pool = GEventPool(threads)
    time_result = do_map(pool.map, work_func, jobs)
    pool.kill()
    return time_result


def thread_pool_executor(work_func: FunctionType, jobs: Sequence[int],
                         threads: int=None, *args, **kwargs):
    """Performs jobs^2 work using concurrent.futures.ThreadPoolExecutor"""
    pool = ThreadPoolExecutor(threads)
    return do_map(pool.map, work_func, jobs)


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.set_start_method('spawn')
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--work-type', '-w', default='compute',
                        choices=['compute', 'network'],
                        help='The kind of work to perform in each pool')
    parser.add_argument('--max-work', '-m', type=int, default=4,
                        help='The power of 2 for number of jobs to execute. '
                             'For example, a choice of 4 will yield a maximum '
                             'of 2^4 jobs to run.')
    parser.add_argument('--samples', '-s', type=int, default=10,
                        help='The total number of samples to compute. '
                             'For example, 4 samples with max-work of 4 will '
                             'run each pool with 4, 8, 12, and then 16 jobs.')
    parser.add_argument('--concurrent-threads', '-t', type=int, default=50,
                        help='The number of concurrent threads to use in '
                             'each thread pool.')
    parser.add_argument('--concurrent-processes', '-p', type=int,
                        default=multiprocessing.cpu_count() * 2 + 1,
                        help='The number of concurrent processes to use in '
                             'each process pool. The default is (number of'
                             'processors * 2) + 1.')
    parser.add_argument('--no-graph', action='store_true', default=False,
                        help='Disable showing the graph of the results at the '
                             'end of execution.')
    args = parser.parse_args()

    if args.samples < 1:
        parser.error("Samples must be a positive integer")

    if args.work_type == 'compute':
        work_func = do_compute_work
    else:
        work_func = do_network_work

    pool_funcs = [
        eventlet_green_pool,
        gevent_green_pool,
        multiprocessing_process_pool,
        multiprocessing_thread_pool,
        thread_pool_executor,
    ]

    max_jobs = 2 ** args.max_work
    samples = args.samples
    job_step = int(max_jobs / samples)
    if job_step == 0:
        job_step = 1
    jobs = range(0, max_jobs + 1, job_step)
    concurrent_threads = args.concurrent_threads
    concurrent_processes = args.concurrent_processes

    print(textwrap.dedent(
        """\
        Pool performance analysis configuration:

        maximum work:         2^{work} = {jobs} jobs
        concurrent processes: {concurrent_processes}
        concurrent threads:   {concurrent_threads}
        number of samples:    {samples}
        """.format(
            work=args.max_work,
            jobs=max_jobs,
            concurrent_threads=concurrent_threads,
            concurrent_processes=concurrent_processes,
            samples=samples,
        )
    ))

    all_results = list(tqdm(
        map(
            lambda pool_func: (
                pool_func.__name__,
                test_pool_func(
                    pool_func,
                    work_func,
                    tqdm(jobs, desc=pool_func.__name__),
                    processes=concurrent_processes,
                    threads=concurrent_threads,
                )
            ),
            pool_funcs
        ),
        desc='Pool Analysis',
        total=len(pool_funcs),
    ))

    print("\n\n")

    all_results_dict = dict(all_results)
    sorted_results = sorted(all_results_dict.keys())
    for name in sorted_results:
        table = tabulate(all_results_dict.get(name), headers='keys',
                         tablefmt='pipe')
        print("{}:\n{}\n\n".format(name, table))

    if args.no_graph is True:
        exit(0)

    from matplotlib import pyplot as plt

    plt.title('Run time and memory usage vs number of jobs')
    # plt.subplot(nrows, ncols, plot_number)
    plt.subplot(2, 1, 1)
    utils.plot_tuple_array(all_results, 'jobs', 'time')
    plt.subplot(2, 1, 2)
    utils.plot_tuple_array(all_results, 'jobs', 'leaked blocks',
                           custom_y_label='memory allocated', y_mapping=cumsum)
    plt.show()
