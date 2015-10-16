from collections import OrderedDict
import re

from tabulate import tabulate

class BenchmarkLog:
    def __init__(self, title, path):
        self.title = title
        r = OrderedDict()
        for line in open(path):
            if 0:
                print(repr(line))
            line = line.replace('test-sources/', '')
            m = re.match('(compare_.+): (.+)', line)
            if m:
                #print('MATCH: %r' % (m.groups(), ))
                stat = m.groups()
                if stat[1].startswith("xgcc '"):
                    stat = stat[0], 'xgcc %s' % stat[1][6:-1]
            m = re.match('Min: (.+)', line)
            if m:
                #print('MATCH: %r' % (m.groups(), ))
                min_ = m.group(1)
                r[stat] = min_
            #m = re.match('Avg: (.+)', line)
            #if m:
            #    #print('MATCH: %r' % (m.groups(), ))
            #    avg = m.groups()
            #    r[stat] = avg
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
    logs.append(BenchmarkLog('v2+packed+ranges',
                             'bmark-v2-plus-compressed-ranges.txt'))
    return logs

logs = read_logs()

print("Minimal wallclock time (s) over 10 iterations")
data = []
for k, v in logs[0].iter_wallclock_items():
    line = [k[1][8:], v]
    for log in logs[1:]:
        line.append(log.get_result(k))
    data.append(line)
print(tabulate(data,
               headers=[''] + ['Control -> %s'
                               % log.title for log in logs]))
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
titles = [log.title for log in logs]
print(tabulate(data, headers=['', 'Control'] + titles))
print('\n')
