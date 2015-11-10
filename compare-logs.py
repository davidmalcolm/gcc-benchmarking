from collections import OrderedDict
import re

from tabulate import tabulate

def median(data):
    if 0:
        print(data)
    data = sorted(data)
    n = len(data)
    if n == 0:
        raise ValueError('no data')
    elif n % 2 == 0:
        return data[n // 2]
    else:
        raise ValueError('TODO')

class BenchmarkLog:
    def __init__(self, title, path):
        self.title = title
        r = OrderedDict()
        stat = None
        for line in open(path):
            if 0:
                print(repr(line))
            line = line.replace('test-sources/', '')
            m = re.match('(compare_.+): (.+)', line)
            if m:
                #print('MATCH: %r' % (m.groups(), ))
                #print('stat: %r' % (stat, ))
                if stat and data['control'] and data['experiment']:
                    old_median = median(data['control'])
                    new_median = median(data['experiment'])
                    if 0:
                        print('Median: %s -> %s' % (old_median, new_median))
                    r[stat] = (old_median, new_median)
                    #print(data)
                data = {'control':[], 'experiment':[]}
                stat = m.groups()
                if stat[1].startswith("xgcc '"):
                    stat = stat[0], 'xgcc %s' % stat[1][6:-1]

            m = re.match('Min: (.+) -> (.+): .*', line)
            if m:
                #print('MATCH: %r' % (m.groups(), ))
                min_ = m.groups()
                # FIXME:
                #r[stat] = min_
            m = re.match('  iteration [0-9]+: (.+): (.+): time_taken: (.+)', line)
            if m:
                if 0:
                    print('MATCH: %r' % (m.groups(), ))
                peer, test, time_taken = m.groups()
                time_taken = float(time_taken)
                #print(time_taken)
                data[peer].append(time_taken)

            m = re.match('Mem max: (.+) -> (.+): .*', line)
            if m:
                r[stat] = m.groups()
        self.dict_ = r

    def iter_wallclock_items(self):
        for k, v in self.dict_.iteritems():
            if k[0] == 'compare_wallclock':
                yield k, v

    def iter_memory_items(self):
        for k, v in self.dict_.iteritems():
            if k[0] == 'compare_memory':
                yield k, v

    def get_result(self, key):
        return self.dict_[key]

def percent_change(result, control):
    amt = (100. * result / control) - 100.
    pc = '%.1f%%' % amt
    if amt >= 0:
        pc = '+' + pc
    return pc

def read_logs():
    logs = []
    logs.append(BenchmarkLog('v2',
                             'bmark-v2.txt'))
    logs.append(BenchmarkLog('v2+every+token',
                             'bmark-v2-plus-adhoc-ranges-for-tokens.txt'))
    logs.append(BenchmarkLog('packed+ranges-1',
                             'bmark-v2-plus-compressed-ranges.txt'))
    logs.append(BenchmarkLog('packed+ranges-2',
                             'bmark-v2-plus-compressed-ranges-v2.txt'))
    logs.append(BenchmarkLog('packed+ranges-2+cp',
                             'bmark-v2-with-cp-expr-ranges.txt'))
    return logs

logs = read_logs()
titles = [log.title for log in logs]
headers=['', 'Control'] + titles

print("Median wallclock time (s) over 10 iterations")
print("  (each experiment's % change is relative to 10 iterations of control interleaved with that experiment)")
data = []
for k, v in logs[0].iter_wallclock_items():
    line = [k[1][8:]]
    control = float(v[0])
    line.append(control)
    for log in logs:
        result = log.get_result(k)
        # We have a (control, experiment) pair of stringified floats;
        # get experiment:
        local_control = round(float(result[0]), 5)
        experiment = round(float(result[1]), 5)
        line.append('%s (%s)'
                    % (experiment,
                       percent_change(experiment, local_control)))
    data.append(line)
print(tabulate(data, headers=headers))
print('\n')

print("Maximal ggc memory (kb)")
data = []
for k, v in logs[0].iter_memory_items():
    line = [k[1][8:]]
    control = float(v[0])
    line.append(int(control))
    for log in logs:
        result = log.get_result(k)
        # We have a (control, experiment) pair of stringified floats;
        # get experiment:
        result = float(result[1])
        line.append('%s (%s)'
                    % (int(result),
                       percent_change(result, control)))
    data.append(line)
print(tabulate(data, headers=headers))
print('\n')
