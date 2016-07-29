#!/usr/bin/python
""" fit world record paces to simple model """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scipy.optimize as optimize
try:
    from util import print_m_s
except ImportError:
    os.sys.path.append('%s' % os.getenv('HOME'))
    from scripts.util import print_m_s

METERS_PER_MILE = 1609.344  # meters
MARATHON_DISTANCE_M = 42195  # meters
MARATHON_DISTANCE_MI = MARATHON_DISTANCE_M / METERS_PER_MILE  # meters


def do_fit(data, func, param_default, do_bootstrap=False):
    """ perform fit """
    datax = data[:, 0]
    datay = data[:, 1]
    popt, pcov = optimize.curve_fit(func, datax, datay, p0=param_default)
    eigval, eigvec = np.linalg.eig(pcov)
    sig = eigvec.dot(np.sqrt(np.diag(eigval))).dot(eigvec.T)
    dpopt = np.sqrt(np.sum(sig.dot(eigvec)**2, axis=1))

    errfunc = lambda popt, x, y: func(x, *popt) - y

    residuals = errfunc(popt, datax, datay)
    s_res = np.std(residuals)
    params = []
    datayerrors = None
    # 100 random data sets are generated and fitted
    for _ in range(100):
        if datayerrors is None:
            random_delta = np.random.normal(0., s_res, len(datay))
            random_data_y = datay + random_delta
        else:
            random_delta = np.array([np.random.normal(0., derr, 1)[0]
                                    for derr in datayerrors])
            random_data_y = datay + random_delta
        randomfit, _ = optimize.leastsq(errfunc, param_default,
                                        args=(datax, random_data_y),
                                        full_output=0)
        params.append(randomfit)

    params = np.array(params)
    mean_pfit = np.mean(params, 0)
    n_sigma = 1.  # 1sigma gets approximately the same as methods above
                  # 1sigma corresponds to 68.3% confidence interval
                  # 2sigma corresponds to 95.44% confidence interval
    err_pfit = n_sigma * np.std(params, 0)

    pfit_bootstrap = mean_pfit
    perr_bootstrap = err_pfit

    if do_bootstrap:
        return popt, dpopt
    else:
        return pfit_bootstrap, perr_bootstrap


def read_result_file(fname):
    """ read file with world record distances/paces """
    running_paces = []
    with open(fname, 'r') as result_file:
        for line in result_file:
            ent = line.split()
            if 'distance' in ent[0]:
                continue
            dist_meters = float(ent[0]) * 1000.
            time_string = ent[1]
            __t__ = [float(x) for x in time_string.split(':')]
            time_sec = __t__[0]*3600 + __t__[1]*60 + __t__[2]
            pace_per_mi = (time_sec / 60.) / (dist_meters / METERS_PER_MILE)
            running_paces.append([dist_meters/METERS_PER_MILE, pace_per_mi])
    return running_paces


def plot_paces():
    """ plot paces with fit """
    running_paces_men = read_result_file('running_world_records_men.txt')
    running_paces_women = read_result_file('running_world_records_women.txt')

    rpm = np.array(running_paces_men)
    rpw = np.array(running_paces_women)

    plt.scatter(np.log(rpm[:, 0]), rpm[:, 1], c='b',
                label='Men\'s World Records')
    plt.scatter(np.log(rpw[:, 0]), rpw[:, 1], c='r',
                label='Women\'s World Records')

    plt.xlim(np.log(60/METERS_PER_MILE), np.log(600e3/METERS_PER_MILE))
    plt.ylim(2, 16)

    # Set x ticks
    xtickarray = np.log(np.array([100, 200, 400, 800, METERS_PER_MILE,
                                  5e3, 10e3,
                                  MARATHON_DISTANCE_M / 2.,
                                  MARATHON_DISTANCE_M,
                                  50 * METERS_PER_MILE,
                                  100 * METERS_PER_MILE,
                                  300 * METERS_PER_MILE]) / METERS_PER_MILE)
    ytickarray = np.array(range(2, 16))

    plt.xticks(xtickarray,
               ['100m', '', '', '800m', '1mi', '5k', '10k', '', 'Marathon',
                '', '100mi', '300mi'])

    # Set y ticks
    plt.yticks(ytickarray, ['%d:00/mi' % x for x in range(3, 16)])

    plt.legend(loc='upper left')

    for xt_ in xtickarray:
        plt.plot([xt_, xt_], [2, 16], color='black', linewidth=0.5,
                 linestyle=':')

    for yt_ in ytickarray:
        plt.plot(np.log([60/METERS_PER_MILE, 600e3/METERS_PER_MILE]),
                 [yt_, yt_], color='black', linewidth=0.5, linestyle=':')

    plt.title('Running Race (minutes per mile) for World Records from 100m '
              'to 48hours')

    mp0 = np.mean(rpm[np.abs(rpm[:, 0]-MARATHON_DISTANCE_MI) < 1][:, 1])
    wp0 = np.mean(rpw[np.abs(rpw[:, 0]-MARATHON_DISTANCE_MI) < 1][:, 1])

    print('men\'s world record pace', print_m_s(mp0*60))
    print('women\'s world record pace', print_m_s(wp0*60))

    def mfunc(xval, *params):
        """ ... """
        xval0 = MARATHON_DISTANCE_M/METERS_PER_MILE
        return mp0*(xval/xval0)**params[0]

    def wfunc(xval, *params):
        """ ... """
        xval0 = MARATHON_DISTANCE_M/METERS_PER_MILE
        return wp0*(xval/xval0)**params[0]

    rpm_low = rpm[rpm[:, 0] <= MARATHON_DISTANCE_MI]
    rpm_high = rpm[rpm[:, 0] > MARATHON_DISTANCE_MI]

    params, dparams = do_fit(rpm_low, mfunc, param_default=[1])
    pp_, pm_ = params+dparams, params-dparams
    print('men\'s')
    print('p', params, '+/-', dparams)

    xval = np.linspace(400, MARATHON_DISTANCE_M, 1000)/METERS_PER_MILE
    plt.plot(np.log(xval), mfunc(xval, *params), 'b', linewidth=2.5)
    plt.plot(np.log(xval), mfunc(xval, *pp_), 'b--')
    plt.plot(np.log(xval), mfunc(xval, *pm_), 'b--')

    params, dparams = do_fit(rpm_high, mfunc, param_default=[1])
    pp_, pm_ = params+dparams, params-dparams
    print('p', params, '+/-', dparams)

    xval = np.linspace(MARATHON_DISTANCE_M, 600e3, 1000)/METERS_PER_MILE
    plt.plot(np.log(xval), mfunc(xval, *params), 'b', linewidth=2.5)
    plt.plot(np.log(xval), mfunc(xval, *pp_), 'b--')
    plt.plot(np.log(xval), mfunc(xval, *pm_), 'b--')

    rpw_low = rpw[rpw[:, 0] <= MARATHON_DISTANCE_MI]
    rpw_high = rpw[rpw[:, 0] > MARATHON_DISTANCE_MI]

    params, dparams = do_fit(rpw_low, wfunc, param_default=[1])
    pp_, pm_ = params+dparams, params-dparams
    print('women\'s')
    print('p', params, '+/-', dparams)

    xval = np.linspace(400, MARATHON_DISTANCE_M, 1000)/METERS_PER_MILE
    plt.plot(np.log(xval), wfunc(xval, *params), 'r', linewidth=2.5)
    plt.plot(np.log(xval), wfunc(xval, *pp_), 'r--')
    plt.plot(np.log(xval), wfunc(xval, *pm_), 'r--')

    params, dparams = do_fit(rpw_high, wfunc, param_default=[1])
    pp_, pm_ = params+dparams, params-dparams
    print('p', params, '+/-', dparams)

    xval = np.linspace(MARATHON_DISTANCE_M, 600e3, 1000)/METERS_PER_MILE
    plt.plot(np.log(xval), wfunc(xval, *params), 'r', linewidth=2.5)
    plt.plot(np.log(xval), wfunc(xval, *pp_), 'r--')
    plt.plot(np.log(xval), wfunc(xval, *pm_), 'r--')

    plt.show()
    plt.savefig('world_record.png')
    os.system('mv world_record.png /home/ddboline/public_html/')

if __name__ == '__main__':
    plot_paces()
