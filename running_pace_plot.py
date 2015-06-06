#!/usr/bin/python3
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from util import print_h_m_s, print_m_s

from world_record import do_fit, METERS_PER_MILE, MARATHON_DISTANCE_M,\
                         MARATHON_DISTANCE_MI

def read_result_file(fname):
    """ read results """
    running_paces = []
    with open(fname, 'rb') as result_file:
        for line in result_file:
            print(type(line))
            ent = line.split()
            dist_meters = float(ent[0])
            pace_minute = int(ent[1])
            pace_second = int(ent[2])
            include_race = int(ent[4])
            time_ = (pace_minute + pace_second/60.)
            if include_race:
                running_paces.append([dist_meters, time_])
    return running_paces

def plot_paces(fname):
    """ plot paces with fit """
    running_paces = read_result_file(fname)
    rp_ = np.array(running_paces)
    plt.scatter(np.log(rp_[:, 0]), rp_[:, 1], label='race results')
    plt.xlim(np.log([0.9, 60]))
    plt.ylim([5, 16])

    # Set x ticks
    xtickarray = np.log(np.array([METERS_PER_MILE, 5e3, 10e3,
                                  MARATHON_DISTANCE_M/2., MARATHON_DISTANCE_M,
                                  50*METERS_PER_MILE])/METERS_PER_MILE)
    ytickarray = np.array([5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])

    plt.xticks(xtickarray, ['1mi', '5k', '10k', '', 'Marathon', '50mi'])

    # Set y ticks
    plt.yticks(ytickarray, ['5:00/mi', '6:00/mi', '7:00/mi', '8:00/mi',
                            '9:00/mi', '10:00/mi', '11:00/mi', '12:00/mi',
                            '13:00/mi', '14:00/mi', '15:00/mi'])

    for xt_ in xtickarray:
        plt.plot([xt_, xt_], [5, 16], color='black', linewidth=0.5,
                 linestyle=':')

    for yt_ in ytickarray:
        plt.plot(np.log([0.9, 60]), [yt_, yt_], color='black', linewidth=0.5,
                 linestyle=':')

    plt.legend(loc='upper left')

    param0 = np.mean(rp_[np.abs(rp_[:, 0]-MARATHON_DISTANCE_MI) < 1][:, 1])
    print('average marathon pace', print_m_s(param0*60))
    pbest = np.min(rp_[np.abs(rp_[:, 0]-MARATHON_DISTANCE_MI) < 1][:, 1])
    print('best marathon pace', print_m_s(pbest*60))
    print('')

    def pow_func(xval, *params):
        """ ... """
        x0_ = MARATHON_DISTANCE_M/METERS_PER_MILE
        return param0*(xval/x0_)**params[0]

    xval = np.linspace(1, MARATHON_DISTANCE_MI, 100)
    rp_low = rp_[rp_[:, 0] < MARATHON_DISTANCE_MI]
    rp_high = rp_[rp_[:, 0] >= MARATHON_DISTANCE_MI]
    params, dparams = do_fit(rp_low, pow_func, param_default=[0.5])
    pp_, pm_ = params+dparams, params-dparams
    plt.plot(np.log(xval), pow_func(xval, *params), 'b', linewidth=2.5)
    plt.plot(np.log(xval), pow_func(xval, *pp_), 'b--')
    plt.plot(np.log(xval), pow_func(xval, *pm_), 'b--')

    print('p', params, '+/-', dparams)
    print('')

    xval = np.linspace(MARATHON_DISTANCE_MI, 60, 100)
    params, dparams = do_fit(rp_high, pow_func, param_default=[0.5])
    pp_, pm_ = params+dparams, params-dparams
    plt.plot(np.log(xval), pow_func(xval, *params), 'b', linewidth=2.5)
    plt.plot(np.log(xval), pow_func(xval, *pp_), 'b--')
    plt.plot(np.log(xval), pow_func(xval, *pm_), 'b--')

    print('p', params, '+/-', dparams)
    print('')

    def pow_func_best(xval, *params):
        """ ... """
        x0_ = MARATHON_DISTANCE_M/METERS_PER_MILE
        return pbest*(xval/x0_)**params[0]

    p50k = pow_func_best(50e3/METERS_PER_MILE, 0.28938393)*60
    p50m = pow_func_best(50, 0.28938393)*60
    print('optimistic 50k estimate', print_m_s(p50k),\
          print_h_m_s(p50k * 50e3/METERS_PER_MILE))
    print('optimistic 50mi estimate', print_m_s(p50m), print_h_m_s(p50m * 50))
    print('')

    p315 = (3*60 + 15) / (MARATHON_DISTANCE_M/METERS_PER_MILE)
    def pow_func_315(xval, *params):
        """ ... """
        x0_ = MARATHON_DISTANCE_M/METERS_PER_MILE
        return p315*(xval/x0_)**params[0]

    p50k = pow_func_315(50e3/METERS_PER_MILE, 0.28938393)*60
    p50m = pow_func_315(50, 0.28938393)*60
    print('3:15 marathon pace', print_m_s(p315*60))
    print('3:15marathon 50k estimate', print_m_s(p50k),\
          print_h_m_s(p50k * 50e3/METERS_PER_MILE))
    print('3:15marathon 50mi estimate', print_m_s(p50m),\
          print_h_m_s(p50m * 50))
    print('')

    p300 = (3*60) / (MARATHON_DISTANCE_M/METERS_PER_MILE)
    def pow_func_300(xval, *params):
        """ ... """
        x0_ = MARATHON_DISTANCE_M/METERS_PER_MILE
        return p300*(xval/x0_)**params[0]

    p50k = pow_func_300(50e3/METERS_PER_MILE, 0.28938393)*60
    p50m = pow_func_300(50, 0.28938393)*60
    print('3:00 marathon pace', print_m_s(p300*60))
    print('3:00marathon 50k estimate', print_m_s(p50k),
          print_h_m_s(p50k * 50e3/METERS_PER_MILE))
    print('3:00marathon 50mi estimate', print_m_s(p50m),
          print_h_m_s(p50m * 50))

    plt.savefig('running_pace.png')

if __name__ == '__main__':
    read_result_file('running_paces.txt')
    plot_paces('running_paces.txt')
