#!/usr/bin/python
from __future__ import print_function

import os
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sklearn import linear_model
import math

HOMEDIR = os.getenv('HOME')

meters_per_mile = 1609.344 # meters
km_per_mile = meters_per_mile / 1000
marathon_distance_m = 42195 # meters
marathon_distance_mi = 42195 / meters_per_mile # meters

class running_pace:
    def __init__(self, d=0.0, pmpm=0.0, y=2014, f=True, name=''):
        self.distance = d
        self.pace = pmpm
        self.year = y
        self.flag = f
        self.name = name

    def read_line(self, line):
        ents = line.split()
        self.distance = float(ents[0])
        m = int(ents[1])
        s = int(ents[2])
        self.pace = float(m) + float(s) / 60.
        self.year = int(ents[3])
        self.flag = int(ents[4])
        self.name = ents[5]

def read_pace_file(fname='%s/scripts/running_paces.txt' % HOMEDIR):
    running_paces = []

    for line in open(fname, 'r').xreadlines():
        r = running_pace()
        r.read_line(line)
        running_paces.append(r)

    return running_paces

# def func(x, a = 1):
    # return a * x**0.06 / 26.2**1.06

# def func(x):
    # return x

def running_pace_regression():
    running_paces = read_pace_file()

    random.shuffle(running_paces)

    p = []
    d = []
    for r in running_paces:
        p.append(math.log(r.pace))
        d.append(math.log(r.distance))

    p = np.array(p)
    d = np.array(d)

    p_train = p[0:50]
    d_train = d[0:50, np.newaxis]
    p_test = p[-50:]
    d_test = d[-50:, np.newaxis]


    p_train = p
    d_train = d[:, np.newaxis]
    p_test = p
    d_test = d[:, np.newaxis]

    regr = linear_model.LinearRegression()
    regr.fit(d_train, p_train)

    # print(dir(regr))
    print(regr.coef_)

    print(np.mean((regr.predict(d_test) - p_test)**2))

    plt.scatter(d_test, p_test, color='black')
    plt.plot(d_test, regr.predict(d_test), color='blue',
            linewidth=3)

    plt.xticks(())
    plt.yticks(())

    plt.savefig('temp.png')

if __name__ == '__main__':
    running_pace_regression()
