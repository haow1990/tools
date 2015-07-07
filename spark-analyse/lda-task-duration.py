#!/usr/bin/env python

import sys
import re
import datetime as dt
import pygal
from pygal.style import Style

taskptn = re.compile(r'^(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+) .* ADD MATRIX .*partId=(\d+)')

def parseLine(line):
  match = taskptn.match(line)
  if match:
    year = int(match.group(1))
    if year < 100:
      year = year + 2000
    month = int(match.group(2))
    day = int(match.group(3))
    hour = int(match.group(4))
    minute = int(match.group(5))
    seconds = int(match.group(6))
    taskid = int(match.group(7))
    timestamp = dt.datetime(year, month, day, hour, minute, seconds)
    return (timestamp, taskid)
  else:
    return (None, None)

def parseFile(infile):
  starttime = None
  endtime = None
  # parse line to retrieve start and end time of tasks
  tasks = {} # taskId -> list of task start or end time
  for line in infile:
    (time, taskid) = parseLine(line)
    if not time:
      continue
    if not starttime or starttime > time:
      starttime = time
    if not endtime or endtime < time:
      endtime = time

    if not tasks.has_key(taskid):
      tasks[taskid] = [time]
    else:
      tasks[taskid].append(time)
    
  newtasks = {} # taskid -> ([start time], [end time])
  totalDuration = int((endtime - starttime).total_seconds())
  for (taskid, timelist) in tasks.items():
    offsets = [int((time - starttime).total_seconds()) for time in timelist]
    offsets.sort()
    starts = [offsets[i] for i in xrange(0, len(offsets), 2)]
    ends = [offsets[i] for i in xrange(1, len(offsets), 2)]
    # log file may be incomplete, if end time is missing,
    # simply assume that it lasts till the end
    if len(ends) + 1 == len(starts):
      ends.append(totalDuration)
    newtasks[taskid] = (starts, ends)

  return (starttime, newtasks)

def createChart(title):
  style = Style(colors=['#00731F', '#00731F'])
  chart = pygal.XY(title=title, style=style, show_legend=False, show_y_labels=False)
  chart.point_label_format = lambda (x, y): '%.4f %s' % (x,y)
  chart.x_title = 'Seconds since start'
  return chart

def draw(path, iteration, tasks, starttime):
  title = 'Task Duration (start = %s)' % starttime
  chart = createChart(title)
  for (taskid, (starts, ends)) in tasks.items():
    s = starts[iteration]
    e = ends[iteration]
    dur = e - s
    label = 'task %s: %ss(%s~%s)' % (taskid, dur, s, e)
    data = [
        {'value': (s, taskid), 'tooltip': label},
        {'value': (e, taskid), 'tooltip': label}
    ]
    chart.add(str(taskid), data)
  chart.render_to_file(path)

def main():
  path = sys.argv[1]
  (starttime, tasks) = parseFile(sys.stdin)
  for i in xrange(2, len(sys.argv)):
    iteration = int(sys.argv[i])
    print 'Generating Iteration', iteration
    draw('%s-%s.svg' % (path, iteration), iteration, tasks, starttime)

if __name__ == '__main__':
  main()

