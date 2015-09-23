import os
import time
import subprocess
import stat
import sys

import perf

class Peer:
    """
    Either the control or the experiment.
    "path" is the path to a built gcc directory, containing
    an "xgcc" binary, "cc1", etc.
    """
    def __init__(self, name, path):
        self.name = name
        self.path = path

    def get_binary(self, binary_name):
        return os.path.join(self.path, binary_name)

    def strip_binaries(self):
        """
        Strip various binaries of debuginfo
        """
        for binary_name in ('xgcc', 'cc1', 'cc1plus', 'collect2'):
            path = self.get_binary(binary_name)
            statinfo = os.stat(path)
            if stat.S_ISREG(statinfo.st_mode) \
               and statinfo.st_mode & stat.S_IXOTH:
                subprocess.call(['strip', path])

class Options:
    def __init__(self, benchmark_name):
        self.benchmark_name = benchmark_name
        self.disable_timelines = False
        self.control_label = 'control'
        self.experiment_label = 'experiment'

def compare_wallclock(control_path, experiment_path, binary_name, args,
                      num_iters=10):
    """
    Take a pair of paths to gcc builds, and a set of other gcc args.
    Return a perf.BenchmarkResult instance
    """
    control = Peer('control', control_path)
    experiment = Peer('experiment', experiment_path)

    data = []
    for peer in [control, experiment]:
        peer.strip_binaries()
        data.append([])

    print('compare_wallclock: %s %r' % (binary_name, ' '.join(args)))
    for iter_idx in range(num_iters):
        for peer_idx, peer in enumerate([control, experiment]):
            sys.stdout.write('iteration %i: %s: %s %r: '
                             % (iter_idx, peer.name, binary_name, ' '.join(args)))
            actual_args = [peer.get_binary(binary_name), '-B', peer.path] + args
            t1 = time.time()
            subprocess.call(actual_args)
            t2 = time.time()
            time_taken = t2 - t1
            sys.stdout.write('time_taken: %r\n' % time_taken)
            data[peer_idx].append(time_taken)

    options = Options('Wallclock time for %s %s'
                      % (binary_name, ' '.join(args)))
    result = perf.CompareMultipleRuns(data[0],
                                      data[1],
                                      options)
    return result

#args = '-c test-sources/kdecore.cc -g'.split()
args = '-c test-sources/empty.c -g'.split()
#args = '-c test-sources/big-code.c -g'.split()
#args = '-c test-sources/influence.i -g'.split()

#TODO: capture memory usage etc
#TODO: capture just the parsing phase

if __name__ == '__main__':
    control_path = sys.argv[1]
    experiment_path = sys.argv[2]
    result = compare_wallclock(control_path, experiment_path, 'xgcc', args)
    print(result)
