#!/usr/bin/python3
""" Fit my race results to linear model """
from __future__ import (absolute_import, division, print_function, unicode_literals)
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


def read_pace_file(fname='running_paces.txt'):
    """ read running paces file """
    running_paces = []

    for line in open(fname, 'r').readlines():
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

    xtickarray = np.log(
        np.array([
            METERS_PER_MILE, 5e3, 10e3, MARATHON_DISTANCE_M / 2., MARATHON_DISTANCE_M, 50 *
            METERS_PER_MILE
        ]) / METERS_PER_MILE)
    ytickarray = np.log(np.array([5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]))

    plt.xticks(xtickarray, ['1mi', '5k', '10k', '', 'Marathon', '50mi'])

    # Set y ticks
    plt.yticks(ytickarray, [
        '5:00/mi', '6:00/mi', '7:00/mi', '8:00/mi', '9:00/mi', '10:00/mi', '11:00/mi', '12:00/mi',
        '13:00/mi', '14:00/mi', '15:00/mi', '16:00/mi', '17:00/mi'
    ])

    plt.savefig('temp.png')


if __name__ == '__main__':
    running_pace_regression()
