# Performance Analysis of Python Pools

## Goal

Analyze time and space usage of multiple Python thread and process pools with increasing job pool sizes.

Pools being tested:

* multiprocessing.pool.ThreadPool
* multiprocessing.pool.Pool
* concurrent.futures.ThreadPoolExecutor
* concurrent.futures.ProcessPoolExecutor
* eventlet.GreenPool
* gevent.pool.Pool

Types of tests:

* io-bound tests will run the following on every job:
```python
# Note: Gevent and Eventlet use a monkey-patched version of
#       requests during their network-bound tests
import requests

def do_network_work(num: float):
    with requests.Session() as s:
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        s.mount('http://', adapter)
        s.get('http://localhost:8080/')
```
* cpu-bound tests will run the following on every job:
```python
from cmath import sqrt

def do_compute_work(num: float):
    return sqrt(sqrt(sqrt(num)))
```

## Methodology

Thread pools are created with 100 threads and process pools are created with 8 processes. The reason for this change in number of workers is because process performance wanes if there are many more processes than processing cores. Threads should behave the same way with _almost_ no regard to their quantity, as long as it remains sane.

We will call an individual runner in the pools a "worker". Workers will run one unit of work at a time. Increasing numbers of tasks will be submitted to each pool and the amount of time the batches take to complete and memory space they use will be recorded. The analysis comes in when seeing how well the pools handle running these tasks and how well they can clean up after finishing some tasks.

## Running your own tests

To run your own tests on these pools, simply install the requirements with `pip3 install -r requirements.txt` and then run `python3 pools.py --help` to figure out which arguments you would like to specify. If you look at the data dumps in the results section, you will see the commands used to run the tests in this report.

In order to run the network tests you must also start a decently performant web server locally. The web server I used is included in this repo. To run it, just run `python3 server.py`.

Be aware that the last step in the test runner is displaying a graph using matplotlib. Their documentation states that graphs do not work very well in virtual environments, so if you run into this issue you can disable the graph with `--no-graph`.

Note: pools.py is written for Python3 to make use of the built-in libraries of futures and multiprocessing as well as the lazily evaluated map functions. It cannot be run with Python2 without significant modification.

## Results

### CPU-bound tests

[Small test](data_dumps/small_compute_bound.md)

![Small compute bound test](data_dumps/small_compute_bound.png)

[Large test](data_dumps/large_compute_bound.md)

![Large compute bound test](data_dumps/large_compute_bound.png)

### IO-bound tests

[Small test](data_dumps/small_network_bound.md)

![Small network bound test](data_dumps/small_network_bound.png)

[Large test](data_dumps/large_network_bound.md)

![Large network bound test](data_dumps/large_network_bound.png)

## Conclusions

Among all 6 different kinds of pools and both workload types, the multiprocessing process pool is the overall winner.

Following very closely behind were the standard library's ThreadPoolExecutor and gevent's pool.
Eventlet's pool and the multiprocessing thread pool were evenly matched overall.
The standard library's process pool failed miserably on completion time for compute, even though it outperformed on time in I/O bound tests; thus, it received last place.

Each pool has a particular function that was performance tested, the IO-bound performance, and the CPU-bound performance. The performance ratings are out of 5 for average performance relative to one another across all tests, higher is better.
These ratings are very general and should not be considered performance metrics, merely a quick and __*potentially opinionated*__ judgement to compare the pools.

### Overall Ranks

The multiprocessing process pool performed the best overall. It wasn't always the fastest pool but it consistently performed on or above-par relative to the other pools. This process pool really shone when run with large quantities of jobs in a I/O-bound environment. Unfortunately, the memory usage could not be tracked correctly and this was taken into account in the below ratings.

Eventlet and gevent often ran their tests very similarly, but differed in a few significant ways. Their test outputs are similar in that they have nearly-equivalent completion times and they also have incredibly stable completion times. These would be good pools to use if one wants deterministic completion times. The first difference is that eventlet consistently used much less memory during the I/O-bound tests. The second major difference is that gevent typically had the faster completion time performance.

The standard library's thread pool fared pretty well in these tests. Its execution time was on-par with several other thread pools' times and its memory usage was similar to those as well. It performed quite similarly to the multiprocessing thread pool, but it did not have the same memory issues present in the multiprocessing thread pool.

The multiprocessing thread pool performed well enough, but suffered from memory issues during the compute-bound tests. Its completion time performance is on-par with most of the other thread pools.

The standard library's process pool seriously underperformed in this kind of compute-bound test. Though not present in the graphs, I observed the pool had been locking up on a single core with 100% utilization during its tests while only some of the compute work was being spread out to its workers. If not for its bad completion times in compute, this process pool may have done very well overall. Its completion times were simply a large multiple longer than most of the other pools. Its memory usage, on the other hand, measured quite low.

* Overall
    - `multiprocessing.pool.Pool`: 4.25/5
    - `concurrent.futures.ThreadPoolExecutor`: 4/5
    - `gevent.pool.Pool`: 4/5
    - `eventlet.GreenPool`: 3.5/5
    - `multiprocessing.pool.ThreadPool`: 3.5/5
    - `concurrent.futures.ProcessPoolExecutor`: 3/5
* CPU-bound tasks
    - `gevent.pool.Pool`: 5/5
    - `eventlet.GreenPool`: 4.5/5
    - `multiprocessing.pool.Pool`: 4/5
    - `concurrent.futures.ThreadPoolExecutor`: 4/5
    - `multiprocessing.pool.ThreadPool`: 3/5
    - `concurrent.futures.ProcessPoolExecutor`: 1/5
* IO-bound tasks
    - `concurrent.futures.ProcessPoolExecutor`: 5/5
    - `multiprocessing.pool.Pool`: 4.5/5
    - `concurrent.futures.ThreadPoolExecutor`: 4/5
    - `multiprocessing.pool.ThreadPool`: 4/5
    - `gevent.pool.Pool`: 3/5
    - `eventlet.GreenPool`: 3/5

### Eventlet Green Pool

* Pool type: thread pool
* Function: `eventlet.GreenPool.imap`
* CPU-bound time: 5/5
* CPU-bound space: 3/5
* IO-bound time: 1/5
* IO-bound space: 5/5

### Gevent Pool

* Pool type: thread pool
* Function: `gevent.pool.Pool.imap_unordered`
* CPU-bound time: 5/5
* CPU-bound space: 5/5
* IO-bound time: 3/5
* IO-bound space: 3/5

### Multiprocessing Process Pool

* Pool type: process pool
* Function: `multiprocessing.pool.Pool.imap_unordered`
* CPU-bound time: 4/5
* CPU-bound space: 3/5
* IO-bound time: 5/5
* IO-bound space: N/A (test inconclusive)

### Multiprocessing Thread Pool

* Pool type: thread pool
* Function: `multiprocessing.pool.ThreadPool.imap_unordered`
* CPU-bound time: 4/5
* CPU-bound space: 1/5
* IO-bound time: 3/5
* IO-bound space: 3/5

### Process Pool Executor

* Pool type: process pool
* Function: `concurrent.futures.ProcessPoolExecutor.map`
* CPU-bound time: 1/5
* CPU-bound space: 2/5
* IO-bound time: 5/5
* IO-bound space: 5/5

### Thread Pool Executor

* Pool type: thread pool
* Function: `concurrent.futures.ThreadPoolExecutor.map`
* CPU-bound time: 4/5
* CPU-bound space: 3/5
* IO-bound time: 3/5
* IO-bound space: 3/5
