#!/usr/bin/python
""" Fit my race results to linear model """
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sklearn import linear_model
import math

HOMEDIR = os.getenv('HOME')

METERS_PER_MILE = 1609.344  # meters
KM_PER_MILE = METERS_PER_MILE / 1000
MARATHON_DISTANCE_M = 42195  # meters
MARATHON_DISTANCE_MI = 42195 / METERS_PER_MILE  # meters


class RunningPace(object):
    """ Class to contain running pace entry """
    def __init__(self, dist=0.0, pmpm=0.0, year=2014, flag=True, name=''):
        self.distance = dist
        self.pace = pmpm
        self.year = year
        self.flag = flag
        self.name = name

    def read_line(self, line):
        """ read line in running_paces.txt file """
        ents = line.split()
        self.distance = float(ents[0])
        minute = int(ents[1])
        second = int(ents[2])
        self.pace = float(minute) + float(second) / 60.
        self.year = int(ents[3])
        self.flag = int(ents[4])
        self.name = ents[5]


def read_pace_file(fname='%s/scripts/running_paces.txt' % HOMEDIR):
    """ read running paces file """
    running_paces = []

    for line in open(fname, 'r').xreadlines():
        rp_ = RunningPace()
        rp_.read_line(line)
        running_paces.append(rp_)

    return running_paces


def running_pace_regression():
    """ run regression """
    running_paces = read_pace_file()

    random.shuffle(running_paces)

    paces = []
    dists = []
    for rp_ in running_paces:
        paces.append(math.log(rp_.pace))
        dists.append(math.log(rp_.distance))

    paces = np.array(paces)
    dists = np.array(dists)

    p_train = paces[0:50]
    d_train = dists[0:50, np.newaxis]
    p_test = paces[-50:]
    d_test = dists[-50:, np.newaxis]

    p_train = paces
    d_train = dists[:, np.newaxis]
    p_test = paces
    d_test = dists[:, np.newaxis]

    regr = linear_model.LinearRegression()
    regr.fit(d_train, p_train)

    print(regr.coef_)

    print(np.mean((regr.predict(d_test) - p_test)**2))

    plt.scatter(d_test, p_test, color='black')
    plt.plot(d_test, regr.predict(d_test), color='blue', linewidth=3)

    plt.xticks(())
    plt.yticks(())

    plt.savefig('temp.png')

if __name__ == '__main__':
    running_pace_regression()
