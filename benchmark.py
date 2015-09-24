from collections import OrderedDict, namedtuple
import os
import re
import subprocess
import stat
import sys
import time

import perf

STAT_FIELDS = ('usr', 'sys', 'wall', 'ggc')
class Stats(namedtuple('Stats', STAT_FIELDS)):
    """
    A line of output from -ftime-report
    """
    pass

class TimeReport(OrderedDict):
    """
    The parsed output from -ftime-report, as an ordered mapping from
    names to Stats instances.
    """
    @classmethod
    def from_stderr(cls, err):
        tr = TimeReport()
        for line in err.splitlines():
            ws = r'\s+'
            timing = r'([0-9]+.[0-9]+)'
            percent = r'.+'
            # e.g. "phase setup             :   0.00 ( 0%) usr   0.00 ( 0%) sys   0.00 ( 0%) wall    1077 kB (91%) ggc"
            m = re.match(r'^ (.*)' + ws + ':'
                         + ws + timing + percent + 'usr'
                         + ws + timing + percent + 'sys'
                         + ws + timing + percent + 'wall'
                         + ws + r'([0-9]+) kB' + percent + 'ggc',
                         line)
            if m:
                stats = Stats(*[float(f) for f in m.groups()[1:]])
                name = m.group(1).strip()
                tr[name] = stats

            # e.g. "TOTAL                 :   0.00             0.00             0.00               1189 kB"
            m = re.match(r'^ TOTAL' + ws + ':' + 3 * (ws + timing) + ws + r'([0-9]+) kB$', line)
            if m:
                stats = Stats(*[float(f) for f in m.groups()])
                tr['TOTAL'] = stats
        return tr

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

def make_test_name(binary_name, args):
    test_name = binary_name
    for arg in args:
        if '/' in arg:
            arg = os.path.basename(arg)
        test_name += ' %s' % arg
    return test_name

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

    test_name = make_test_name(binary_name, args)

    print('compare_wallclock: %s' % test_name)
    for iter_idx in range(num_iters):
        for peer_idx, peer in enumerate([control, experiment]):
            sys.stdout.write('  iteration %i: %s: %s: '
                             % (iter_idx, peer.name, test_name))
            sys.stdout.flush()
            actual_args = [peer.get_binary(binary_name), '-B', peer.path] + args
            t1 = time.time()
            subprocess.call(actual_args)
            t2 = time.time()
            time_taken = t2 - t1
            sys.stdout.write('time_taken: %r\n' % time_taken)
            sys.stdout.flush()
            data[peer_idx].append(time_taken)

    options = Options('Wallclock time for %s' % test_name)
    result = perf.CompareMultipleRuns(data[0],
                                      data[1],
                                      options)
    return result

def compare_memory(control_path, experiment_path, binary_name, args,
                   num_iters=3):
    """
    Take a pair of paths to gcc builds, and a set of other gcc args.
    Return a perf.MemoryUsageResult instance
    """
    control = Peer('control', control_path)
    experiment = Peer('experiment', experiment_path)

    data = []
    for peer in [control, experiment]:
        peer.strip_binaries()
        data.append([])

    test_name = make_test_name(binary_name, args)

    print('compare_memory: %s' % test_name)
    for iter_idx in range(num_iters):
        for peer_idx, peer in enumerate([control, experiment]):
            sys.stdout.write('  iteration %i: %s: %s: '
                             % (iter_idx, peer.name, test_name))
            sys.stdout.flush()
            actual_args = [peer.get_binary(binary_name), '-B', peer.path] + args
            actual_args.append('-ftime-report')
            #print(actual_args)
            p = subprocess.Popen(actual_args, stderr=subprocess.PIPE)
            out, err = p.communicate()
            time_report = TimeReport.from_stderr(err)
            total_ggc = time_report['TOTAL'].ggc
            sys.stdout.write('total_ggc: %r KB\n' % total_ggc)
            sys.stdout.flush()
            data[peer_idx].append(total_ggc)

    options = Options('Total ggc memory usage for %s'
                      % test_name)
    result = perf.CompareMemoryUsage(data[0],
                                     data[1],
                                     options)
    return result

#TODO: capture just the parsing phase


def main():
    control_path = sys.argv[1]
    experiment_path = sys.argv[2]
    args_list = ['-S test-sources/kdecore.cc -g',
                 '-S test-sources/empty.c -g',
                 '-S test-sources/big-code.c -g',
                 '-S test-sources/influence.i -g'
    ]
    t1 = time.time()
    for args_str in args_list:
        for opt in ['-O0', '-O1', '-O2', '-O3', '-Os']:
            args = args_str.split()
            args.append(opt)

            result = compare_wallclock(control_path, experiment_path,
                                       'xgcc', args)
            print(result)
            print('\n')

            result = compare_memory(control_path, experiment_path,
                                       'xgcc', args)
            print(result)
            print('\n')

    t2 = time.time()
    time_taken = t2 - t1
    print('total time taken: %r' % time_taken)

if __name__ == '__main__':
    main()
