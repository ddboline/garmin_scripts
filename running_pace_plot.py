#!/usr/bin/python

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scipy.optimize as optimize
from util import print_h_m_s, print_m_s

meters_per_mile = 1609.344 # meters
marathon_distance_m = 42195 # meters
marathon_distance_mi = marathon_distance_m / meters_per_mile # meters

def lin_func(x, *p):
    return p[0] + p[1] * x + p[2] * x**2

def do_fit(data, func, p0):
    datax = data[:, 0]
    datay = data[:, 1]
    p, c = optimize.curve_fit(func, datax, datay, p0=p0)
    l, v = np.linalg.eig(c)
    sig = v.dot(np.sqrt(np.diag(l))).dot(v.T)
    dp = np.sqrt(np.sum(sig.dot(v)**2, axis=1))

    errfunc = lambda p, x, y: func(x, *p) - y

    residuals = errfunc(p, datax, datay)
    s_res = np.std(residuals)
    ps = []
    datayerrors = None
    # 100 random data sets are generated and fitted
    for _ in range(100):
        if datayerrors is None:
            randomDelta = np.random.normal(0., s_res, len(datay))
            randomdataY = datay + randomDelta
        else:
            randomDelta = np.array([\
                               np.random.normal(0., derr, 1)[0] \
                               for derr in datayerrors])
            randomdataY = datay + randomDelta
        randomfit, randomcov = \
            optimize.leastsq(errfunc, p0, args=(datax, randomdataY),\
                              full_output=0)
        ps.append(randomfit)

    ps = np.array(ps)
    mean_pfit = np.mean(ps, 0)
    Nsigma = 1. # 1sigma gets approximately the same as methods above
                # 1sigma corresponds to 68.3% confidence interval
                # 2sigma corresponds to 95.44% confidence interval
    err_pfit = Nsigma * np.std(ps, 0)

    pfit_bootstrap = mean_pfit
    perr_bootstrap = err_pfit

    return p, dp
    # return pfit_bootstrap, perr_bootstrap

def read_result_file(fname):
    running_paces = []
    f = open(fname, 'r')
    for line in f:
        e = line.split()
        dist_meters = float(e[0])
        pace_minute = int(e[1])
        pace_second = int(e[2])
        race_year = int(e[3])
        include_race = int(e[4])
        race_name = ' '.join(e[5:])
        t = (pace_minute + pace_second/60.)
        if include_race:
            running_paces.append([dist_meters, t])

    rp = np.array(running_paces)
    #p, dp = do_fit(rp, lin_func, p0=[1, 1, 1])
    #pp, pm = p+dp, p-dp
    plt.scatter(np.log(rp[:, 0]), rp[:, 1], label='race results')
    plt.xlim(np.log([0.9, 60]))
    plt.ylim([5, 16])

    # Set x ticks
    xtickarray = np.log(np.array([meters_per_mile, 5e3, 10e3, marathon_distance_m/2., marathon_distance_m, 50*meters_per_mile])/meters_per_mile)
    ytickarray = np.array([5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])

    plt.xticks(xtickarray, ['1mi', '5k','10k', '', 'Marathon', '50mi'])

    # Set y ticks
    plt.yticks(ytickarray, ['5:00/mi', '6:00/mi', '7:00/mi', '8:00/mi', '9:00/mi', '10:00/mi', '11:00/mi', '12:00/mi', '13:00/mi', '14:00/mi', '15:00/mi'])

    for xt in xtickarray:
        plt.plot([xt, xt], [5, 16], color='black', linewidth=0.5, linestyle=':')

    for yt in ytickarray:
        plt.plot(np.log([0.9,60]), [yt, yt], color='black', linewidth=0.5, linestyle=':')

    plt.legend(loc='upper left')

    p0 = np.mean(rp[np.abs(rp[:,0]-marathon_distance_mi)<1][:,1])
    print 'average marathon pace',print_m_s(p0*60)
    pbest = np.min(rp[np.abs(rp[:,0]-marathon_distance_mi)<1][:,1])
    print 'best marathon pace',print_m_s(pbest*60)
    print ''

    def pow_func(x, *p):
        x0 = marathon_distance_m/meters_per_mile
        return p0*(x/x0)**p[0]

    x = np.linspace(1, marathon_distance_mi, 100)
    rp_low = rp[rp[:, 0] < marathon_distance_mi]
    rp_high = rp[rp[:, 0] >= marathon_distance_mi]
    p, dp = do_fit(rp_low, pow_func, p0=[0.5])
    pp, pm = p+dp, p-dp
    plt.plot(np.log(x), pow_func(x, *p), 'b', linewidth=2.5)
    plt.plot(np.log(x), pow_func(x, *pp), 'b--')
    plt.plot(np.log(x), pow_func(x, *pm), 'b--')

    print 'p',p,'+/-',dp
    print ''

    x = np.linspace(marathon_distance_mi, 60, 100)
    p, dp = do_fit(rp_high, pow_func, p0=[0.5])
    pp, pm = p+dp, p-dp
    plt.plot(np.log(x), pow_func(x, *p), 'b', linewidth=2.5)
    plt.plot(np.log(x), pow_func(x, *pp), 'b--')
    plt.plot(np.log(x), pow_func(x, *pm), 'b--')

    print 'p',p,'+/-',dp
    print ''

    def pow_func_best(x, *p):
        x0 = marathon_distance_m/meters_per_mile
        return pbest*(x/x0)**p[0]

    p50k = pow_func_best(50e3/meters_per_mile, 0.28938393)*60
    p50m = pow_func_best(50, 0.28938393)*60
    print 'optimistic 50k estimate', print_m_s(p50k), print_h_m_s(p50k * 50e3/meters_per_mile)
    print 'optimistic 50mi estimate', print_m_s(p50m), print_h_m_s(p50m * 50)
    print ''

    p315 = (3*60 + 15) / (marathon_distance_m/meters_per_mile)
    def pow_func_315(x, *p):
        x0 = marathon_distance_m/meters_per_mile
        return p315*(x/x0)**p[0]

    p50k = pow_func_315(50e3/meters_per_mile, 0.28938393)*60
    p50m = pow_func_315(50, 0.28938393)*60
    print '3:15 marathon pace', print_m_s(p315*60)
    print '3:15marathon 50k estimate', print_m_s(p50k), print_h_m_s(p50k * 50e3/meters_per_mile)
    print '3:15marathon 50mi estimate', print_m_s(p50m), print_h_m_s(p50m * 50)
    print ''

    p300 = (3*60) / (marathon_distance_m/meters_per_mile)
    def pow_func_300(x, *p):
        x0 = marathon_distance_m/meters_per_mile
        return p300*(x/x0)**p[0]

    p50k = pow_func_300(50e3/meters_per_mile, 0.28938393)*60
    p50m = pow_func_300(50, 0.28938393)*60
    print '3:00 marathon pace', print_m_s(p300*60)
    print '3:00marathon 50k estimate', print_m_s(p50k), print_h_m_s(p50k * 50e3/meters_per_mile)
    print '3:00marathon 50mi estimate', print_m_s(p50m), print_h_m_s(p50m * 50)

    plt.savefig('running_pace.png')

if __name__ == '__main__':
    read_result_file('running_paces.txt')
