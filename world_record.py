#!/usr/bin/python

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scipy.optimize as optimize
try:
    from util import print_h_m_s, print_m_s
except ImportError:
    os.sys.path.append('%s' % os.getenv('HOME'))
    from scripts.util import print_h_m_s, print_m_s

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

    # print 'p', p
    # print 'pb', pfit_bootstrap
    # print 'dp', dp
    # print 'dpb', perr_bootstrap

    return p, dp
    # return pfit_bootstrap, perr_bootstrap

def read_result_file(fname):
    running_paces = []
    f = open(fname, 'r')
    for line in f:
        e = line.split()
        if 'distance' in e[0]:
            continue
        dist_meters = float(e[0]) * 1000.
        time_string = e[1]
        __t__ = map(float, time_string.split(':'))
        time_sec = __t__[0]*3600 + __t__[1]*60 + __t__[2]
        pace_per_mi = (time_sec / 60.) / (dist_meters / meters_per_mile)
        #print dist_meters, pace_per_mi
        running_paces.append([dist_meters/meters_per_mile, pace_per_mi])
    f.close()
    return running_paces

def plot_paces():
    running_paces_men = read_result_file('running_world_records_men.txt')
    running_paces_women = read_result_file('running_world_records_women.txt')

    rpm = np.array(running_paces_men)
    rpw = np.array(running_paces_women)

    plt.scatter(np.log(rpm[:, 0]), rpm[:, 1], c='b', label='Men\'s World Records')
    plt.scatter(np.log(rpw[:, 0]), rpw[:, 1], c='r', label='Women\'s World Records')

    plt.xlim(np.log(60/meters_per_mile), np.log(600e3/meters_per_mile))
    plt.ylim(2, 12)

    # Set x ticks
    xtickarray = np.log(np.array([100, 200, 800, 5e3, 10e3,marathon_distance_m/2., marathon_distance_m, 160e3, 300*meters_per_mile])/meters_per_mile)
    ytickarray = np.array([3, 4, 5, 6, 7, 8, 9, 10, 11])

    plt.xticks(xtickarray,
               ['100m', '200m', '800m', '5k','10k', '', 'Marathon', '100mi', '300mi'])

    # Set y ticks
    plt.yticks(ytickarray, ['3:00/mi', '4:00/mi', '5:00/mi', '6:00/mi', '7:00/mi', '8:00/mi', '9:00/mi', '10:00/mi', '11:00/mi'])

    plt.legend(loc='upper left')

    for xt in xtickarray:
        plt.plot([xt, xt], [2, 12], color='black', linewidth=0.5, linestyle=':')

    for yt in ytickarray:
        plt.plot([np.log(60/meters_per_mile), np.log(600e3/meters_per_mile)], [yt, yt], color='black', linewidth=0.5, linestyle=':')

    plt.title('Running Race (minutes per mile) for World Records from 100m to 48hours')

    mp0 = np.mean(rpm[np.abs(rpm[:,0]-marathon_distance_mi)<1][:,1])
    wp0 = np.mean(rpw[np.abs(rpw[:,0]-marathon_distance_mi)<1][:,1])

    print 'men\'s world record pace', print_m_s(mp0*60)
    print 'women\'s world record pace', print_m_s(wp0*60)

    def mfunc(x, *p):
        x0 = marathon_distance_m/meters_per_mile
        return mp0*(x/x0)**p[0]

    def wfunc(x, *p):
        x0 = marathon_distance_m/meters_per_mile
        return wp0*(x/x0)**p[0]

    rpm_low = rpm[rpm[:,0] <=marathon_distance_mi]
    rpm_high = rpm[rpm[:,0] >marathon_distance_mi]

    p, dp = do_fit(rpm_low, mfunc, p0=[1])
    pp, pm = p+dp, p-dp
    print 'men\'s'
    print 'p',p,'+/-',dp

    x = np.linspace(400, marathon_distance_m, 1000)/meters_per_mile
    plt.plot(np.log(x), mfunc(x, *p), 'b', linewidth=2.5)
    plt.plot(np.log(x), mfunc(x, *pp), 'b--')
    plt.plot(np.log(x), mfunc(x, *pm), 'b--')

    p, dp = do_fit(rpm_high, mfunc, p0=[1])
    pp, pm = p+dp, p-dp
    print 'p',p,'+/-',dp

    x = np.linspace(marathon_distance_m, 600e3, 1000)/meters_per_mile
    plt.plot(np.log(x), mfunc(x, *p), 'b', linewidth=2.5)
    plt.plot(np.log(x), mfunc(x, *pp), 'b--')
    plt.plot(np.log(x), mfunc(x, *pm), 'b--')

    rpw_low = rpw[rpw[:,0] <=marathon_distance_mi]
    rpw_high = rpw[rpw[:,0] >marathon_distance_mi]

    p, dp = do_fit(rpw_low, wfunc, p0=[1])
    pp, pm = p+dp, p-dp
    print 'women\'s'
    print 'p',p,'+/-',dp

    x = np.linspace(400, marathon_distance_m, 1000)/meters_per_mile
    plt.plot(np.log(x), wfunc(x, *p), 'r', linewidth=2.5)
    plt.plot(np.log(x), wfunc(x, *pp), 'r--')
    plt.plot(np.log(x), wfunc(x, *pm), 'r--')

    p, dp = do_fit(rpw_high, wfunc, p0=[1])
    pp, pm = p+dp, p-dp
    print 'p',p,'+/-',dp

    x = np.linspace(marathon_distance_m, 600e3, 1000)/meters_per_mile
    plt.plot(np.log(x), wfunc(x, *p), 'r', linewidth=2.5)
    plt.plot(np.log(x), wfunc(x, *pp), 'r--')
    plt.plot(np.log(x), wfunc(x, *pm), 'r--')

    plt.show()
    plt.savefig('world_record.png')

if __name__ == '__main__':
    plot_paces()
