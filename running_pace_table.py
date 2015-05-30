#!/usr/bin/python

import os
#import scitools.std
#from scipy.optimize import leastsq
#from scipy.optimize import curve_fit
#import scipy
from util import print_h_m_s, print_m_s

HOMEDIR = os.getenv('HOME')

paces = []

def print_time(pace, dist):
    print print_m_s(pace), print_h_m_s(dist * pace)

def print_time_a_b_c_d_e_f(dist_a, pace_a, dist_b, pace_b, dist_c, pace_c, dist_d, pace_d, dist_e, pace_e, dist_f, pace_f):
    print '\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (print_m_s(pace_a), print_h_m_s(dist_a * pace_a), print_m_s(pace_b), print_h_m_s(dist_b * pace_b), print_m_s(pace_c), print_h_m_s(dist_c * pace_c), print_m_s(pace_d), print_h_m_s(dist_d * pace_d), print_m_s(pace_e), print_h_m_s(dist_e * pace_e), print_m_s(pace_f), print_h_m_s(dist_f * pace_f))

def running_pace(do_plotting=False):
    #print 'pace \t\t marathon \t 25K \t\t half_marathon \t 10mi \t\t 10k \t\t 4mi \t\t 5k'
    #print 'pace \t\t 400m \t 5k \t\t 4mi \t\t 5mi \t\t 10k \t\t 10mi \t\t half_marathon \t marathon'
    print 'pace \t\t 400m \t 800m \t 1200m \t 4mi \t\t 5mi \t\t 8mi \t\t half_marathon \t marathon \t 50mi'
    print '----------------------------------------------------------------------------------------------------------'

    meters_per_mile = 1609.344 # meters
    km_per_mile = meters_per_mile / 1000
    marathon_distance_m = 42195 # meters
    marathon_distance_mi = 42195 / meters_per_mile # meters
    pace_every_two_miles = []
    pace_every_five_k = []
    for mi in range(10, 26, 2):
        pace_every_two_miles.append([mi, ''])
    for km in range(5, 35, 5) + [50]+ [80]:
        mi = km / km_per_mile
        pace_every_five_k.append([mi, ''])

    pace_every_five_k_later = []
    for km in range(35, 75, 5):
        mi = km / km_per_mile
        pace_every_five_k_later.append([mi, ''])

    paumanok_pursuit_legs = [10.75, 8.5, 10.0, 7.5, 6.75]
    bear_mountain_legs = [3.9, 4.7, 5.0, 4.3, 2.7, 4.4, 2.5, 2.8]
    greenbelt_legs = [3.3, 2.9, 2.8, 2.8, 2.9, 2.9, 2.9, 2.8, 2.8, 2.9, 2.9]
    o2s50_legs = [6.0, 6.0, 6.3, 5.8, 6.2, 5.4, 7, 6.4]
    jfk50_legs = [2.5, 6.8, 6.2, 11.6, 7.3, 4, 3.4, 4.2, 4.2]

    dist_o2s50 = []
    dist_o2s50_cum = []
    pace_o2s50_cum = []
    mi = 0
    for leg in o2s50_legs:
        mi += leg
        dist_o2s50.append(leg)
        dist_o2s50_cum.append(mi)
        pace_o2s50_cum.append([mi, ''])

    dist_jfk50 = []
    dist_jfk50_cum = []
    pace_jfk50_cum = []
    mi = 0
    for leg in jfk50_legs:
        mi += leg
        dist_jfk50.append(leg)
        dist_jfk50_cum.append(mi)
        pace_jfk50_cum.append([mi, ''])

    for second in range(4*60+50, 15*60, 10):
        pace = print_h_m_s(second)
        four_hundred_meter = print_m_s(second * 400 / meters_per_mile)
        eight_hundred_meter = print_m_s(second * 800 / meters_per_mile)
        twelve_hundred_meter = print_m_s(second * 1200 / meters_per_mile)
        marathon = print_h_m_s(marathon_distance_mi * second)
        half_marathon = print_h_m_s(marathon_distance_mi/2. * second)
        ten_mile = print_h_m_s(10 * second)
        ten_k = print_h_m_s(10/km_per_mile * second)
        four_mi = print_h_m_s(4 * second)
        five_mi = print_h_m_s(5 * second)
        eight_mi = print_h_m_s(8 * second)
        five_k = print_h_m_s(5/km_per_mile * second)
        fifty_mi = print_h_m_s(50 * second)
        print '%s \t %s \t %s \t %s \t %s \t %s \t %s \t %s \t %s \t %s' % (pace, four_hundred_meter, eight_hundred_meter, twelve_hundred_meter, four_mi, five_mi, eight_mi, half_marathon, marathon, fifty_mi)

    print '\n\n'

    print 'pace \t\t 10mi \t\t 12mi \t\t 14mi \t\t 16mi \t\t 18mi \t\t 20mi \t\t 22mi \t\t 24mi'
    print '------------------------------------------------------------------------------------------'

    for second in range(4*60+50, 16*60, 10):
        pace = print_h_m_s(second)
        print '%s \t' % pace,
        for idx in range(0, len(pace_every_two_miles)):
            pace_every_two_miles[idx][1] = print_h_m_s(pace_every_two_miles[idx][0]* second)
            print '%s \t' % pace_every_two_miles[idx][1],
        print ''

    print '\n\n'

    print 'pace \t\t 5km \t\t 10km \t\t 15km \t\t 20km \t\t 25km \t\t 30km \t\t 50km \t\t 80km'
    print '------------------------------------------------------------------------------------------'
    for second in range(4*60+50, 15*60, 10):
        pace = print_h_m_s(second)
        print '%s \t' % pace,
        for idx in range(0, len(pace_every_five_k)):
            pace_every_five_k[idx][1] = print_h_m_s(pace_every_five_k[idx][0]* second)
            print '%s \t' % pace_every_five_k[idx][1],
        print ''

    print '\n\n'

    print 'pace \t\t 35km \t\t 40km \t\t 45km \t\t 50km \t\t 55km \t\t 60km \t\t 65km \t\t 80km'
    print '------------------------------------------------------------------------------------------'
    for second in range(4*60+50, 16*60, 10):
        pace = print_h_m_s(second)
        print '%s \t' % pace,
        for idx in range(0, len(pace_every_five_k_later)):
            pace_every_five_k_later[idx][1] = print_h_m_s(pace_every_five_k_later[idx][0]* second)
            print '%s \t' % pace_every_five_k_later[idx][1],
        print ''

    print '\n\n'

    #print 'Paumanok Pursuit Time per leg'
    #print 'pace \t\t',
    #for dist in dist_paumanok_pursuit:
            #print '%0.1fmi \t\t' % dist,
    #print ''
    #print '------------------------------------------------------------------------------------------'
    #for second in range(4*60+50, 17*60, 10):
        #pace = print_h_m_s(second)
        #print '%s \t' % pace,
        #for idx in range(0,len(pace_paumanok_pursuit)):
            #pace_paumanok_pursuit[idx][1] = print_h_m_s(pace_paumanok_pursuit[idx][0]* second)
            #print '%s \t' % pace_paumanok_pursuit[idx][1],
        #print ''

    #print '\n\n'

    #print 'Paumanok Pursuit Cumulative Time'
    #print 'pace \t\t',
    #for dist in dist_paumanok_pursuit_cum:
            #print '%0.1fmi \t\t' % dist,
    #print ''
    #print '------------------------------------------------------------------------------------------'
    #for second in range(4*60+50, 17*60, 10):
        #pace = print_h_m_s(second)
        #print '%s \t' % pace,
        #for idx in range(0,len(pace_paumanok_pursuit_cum)):
            #pace_paumanok_pursuit_cum[idx][1] = print_h_m_s(pace_paumanok_pursuit_cum[idx][0]* second)
            #print '%s \t' % pace_paumanok_pursuit_cum[idx][1],
        #print ''

    #print '\n\n'

    #print 'NF Endurance Challenge 50k Cumulative Time'
    #print '     \t\t',
    #for dist in dist_bear_mountain:
            #print '%0.1fmi \t\t' % dist,
    #print ''
    #print 'pace \t\t',
    #for dist in dist_bear_mountain_cum:
            #print '%0.1fmi \t\t' % dist,
    #print ''
    #print '------------------------------------------------------------------------------------------'
    #for second in range(4*60+50, 17*60, 10):
        #pace = print_h_m_s(second)
        #print '%s \t' % pace,
        #for idx in range(0,len(pace_bear_mountain_cum)):
            #pace_bear_mountain_cum[idx][1] = print_h_m_s(pace_bear_mountain_cum[idx][0]* second)
            #print '%s \t' % pace_bear_mountain_cum[idx][1],
        #print ''

    #print '\n\n'

    # print 'Ocean2Sound 50mi Cumulative Time'
    # print '%10s' % '',
    # for dist in dist_o2s50:
    #     print '%6s%4s' % ('%0.1fmi' % dist, ''),
    # print ''
    # print 'pace%6s' % '',
    # for dist in dist_o2s50_cum:
    #     print '%6s%4s' % ('%0.1fmi' % dist, ''),
    # print ''
    # for a in range(0, 120):
    #     os.sys.stdout.write('-')
    #     os.sys.stdout.flush()
    # print ''
    # for second in range(4*60+50, 17*60, 10):
    #     pace = print_h_m_s(second)
    #     print '%8s%2s' % (pace, ''),
    #     for idx in range(0, len(pace_o2s50_cum)):
    #         pace_o2s50_cum[idx][1] = print_h_m_s(pace_o2s50_cum[idx][0]* second)
    #         #print '%s ' % pace_o2s50_cum[idx][1],
    #         print '%8s%2s' % (pace_o2s50_cum[idx][1], ''),
    #     print ''

    # print '\n\n'

    # print 'JFK 50mi Cumulative Time'
    # print '%10s' % '',
    # for dist in dist_jfk50:
    #     print '%6s%4s' % ('%0.1fmi' % dist, ''),
    # print ''
    # print 'pace%6s' % '',
    # for dist in dist_jfk50_cum:
    #     print '%6s%4s' % ('%0.1fmi' % dist, ''),
    # print ''
    # for a in range(0, 120):
    #     os.sys.stdout.write('-')
    #     os.sys.stdout.flush()
    # print ''
    # for second in range(4*60+50, 17*60, 10):
    #     pace = print_h_m_s(second)
    #     print '%8s%2s' % (pace, ''),
    #     for idx in range(0, len(pace_jfk50_cum)):
    #         pace_jfk50_cum[idx][1] = print_h_m_s(pace_jfk50_cum[idx][0]* second)
    #         #print '%s ' % pace_jfk50_cum[idx][1],
    #         print '%8s%2s' % (pace_jfk50_cum[idx][1], ''),
    #     print ''

    # print '\n\n'

def fit_to_pace_file():
    if os.path.exists('running_paces.txt'):
        pace_file = open('running_paces.txt', 'r')
    elif os.path.exists('%s/scripts/running_paces.txt' % HOMEDIR):
        pace_file = open('%s/scripts/running_paces.txt' % HOMEDIR, 'r')
    else:
        exit(0)

    distances = []
    paces = []
    fit_distance = []
    fit_pace = []
    fit_dist_pace = []
    dist_mar_pred = []
    for line in pace_file:
        ent = line.strip().split()
        if len(ent) < 2:
            continue
        distance = float(ent[0])
        pace_min = float(ent[1])
        pace_sec = float(ent[2])
        year = int(ent[3])
        use_race = int(ent[4])
        pace = pace_min + pace_sec / 60.
        marathon_predict = distance * (pace * 60) * (marathon_distance_mi / distance) ** 1.06
        tenmi_pred = distance * (pace * 60) * (10.0 / distance) ** 1.06
        half_marathon_pred = distance * (pace * 60) * (marathon_distance_mi / 2. / distance) ** 1.06
        twentyfivek_pred = distance * (pace * 60) * (25000 / meters_per_mile / distance) ** 1.06
        tenk_pred = distance * (pace * 60) * (10000 / meters_per_mile / distance) ** 1.06
        fivek_pred = distance * (pace * 60) * (5000 / meters_per_mile / distance) ** 1.06
        onemile_pred = distance * (pace * 60) * (1. / distance) ** 1.06
        fiftyk_pred = distance * (pace * 60) * (50000 / meters_per_mile / distance) ** 1.06
        fiftymi_pred = distance * (pace * 60) * (50.0 / distance) ** 1.06
        dist_mar_pred.append([marathon_predict, distance, (pace * 60), half_marathon_pred, twentyfivek_pred, tenmi_pred, tenk_pred, fivek_pred, onemile_pred, fiftyk_pred, fiftymi_pred])
        distances.append(distance)
        paces.append(pace)
        if distance < 20 and use_race > 0:
            fit_dist_pace.append([distance, pace])
            fit_distance.append(distance)
            fit_pace.append(pace)

    os.sys.path.append('/usr/lib/x86_64-linux-gnu/root5.34/')
    from ROOT import TGraph, TF1, kRed, kBlue #, TMatrixDSymEigen
    max_mile = 60
    graph = TGraph()
    graphlog = TGraph()
    for idx in range(0, len(distances)):
        graph.SetPoint(idx, distances[idx], paces[idx])
        import math
        graphlog.SetPoint(idx, math.log(distances[idx]), math.log(paces[idx]))
        idx += 1

    #print dir(graph)
    linfit = graph.Fit('pol1', 'SQ', '', 0, max_mile)
    covmat = linfit.GetCovarianceMatrix()
    flin0 = graph.GetFunction('pol1').Clone()
    flinp = TF1('flinp', '[0]+[1]*x + TMath::Sqrt([2]+ [3]*x + [4]*x**2)', 0, max_mile)
    flinn = TF1('flinn', '[0]+[1]*x - TMath::Sqrt([2]+ [3]*x + [4]*x**2)', 0, max_mile)
    flinp.SetParameters(flin0.GetParameter(0), flin0.GetParameter(1), covmat[0][0], covmat[1][0], covmat[1][1])
    flinn.SetParameters(flin0.GetParameter(0), flin0.GetParameter(1), covmat[0][0], covmat[1][0], covmat[1][1])
    fpow = TF1('fpow', '[0]* (x**0.06) / (26.2**1.06)', 0, max_mile)
    fpowp = TF1('fpow', '[0]* (x**0.06) / (26.2**1.06)', 0, max_mile)
    fpown = TF1('fpow', '[0]* (x**0.06) / (26.2**1.06)', 0, max_mile)
    fpow.SetParameter(0, 1)
    powfit = graph.Fit('fpow', 'Q')
    fpow0 = graph.GetFunction('fpow').Clone()
    fpowp.SetParameter(0, fpow0.GetParameter(0) + fpow0.GetParError(0))
    fpown.SetParameter(0, fpow0.GetParameter(0) - fpow0.GetParError(0))

    print ''
    print '\t10K\t\t\thalf marathon\t\t25K\t\t\tmarathon\t\t50k\t\t\t50mi'
    print '--------------------------------------------------------------------------------------------------------'
    tenk = 10000/meters_per_mile
    twentyfivek = 25000/meters_per_mile
    fiftyk = 50000/meters_per_mile
    for funcn, func0, funcp in [[flinn, flin0, flinp], [fpown, fpow0, fpowp]]:
        print_time_a_b_c_d_e_f(tenk, funcn.Eval(tenk) * 60,
                            marathon_distance_mi/2., funcn.Eval(marathon_distance_mi/2.) * 60,
                            twentyfivek, funcn.Eval(twentyfivek) * 60,
                            marathon_distance_mi, funcn.Eval(marathon_distance_mi) * 60,
                            fiftyk, funcn.Eval(fiftyk) * 60,
                            50.0, funcn.Eval(50.0) * 60)
        print_time_a_b_c_d_e_f(tenk, func0.Eval(tenk) * 60,
                            marathon_distance_mi/2., func0.Eval(marathon_distance_mi/2.) * 60,
                            twentyfivek, func0.Eval(twentyfivek) * 60,
                            marathon_distance_mi, func0.Eval(marathon_distance_mi) * 60,
                            fiftyk, func0.Eval(fiftyk) * 60,
                            50.0, func0.Eval(50.0) * 60)
        print_time_a_b_c_d_e_f(tenk, funcp.Eval(tenk) * 60,
                            marathon_distance_mi/2., funcp.Eval(marathon_distance_mi/2.) * 60,
                            twentyfivek, funcp.Eval(twentyfivek) * 60,
                            marathon_distance_mi, funcp.Eval(marathon_distance_mi) * 60,
                            fiftyk, funcp.Eval(fiftyk) * 60,
                            50.0, funcp.Eval(50.0) * 60)
        print ''

    dist_mar_pred.sort()
    print 'dist\t5k\t\t10k\t\t10mi\t\t1/2 marathon\t25k\t\tmarathon\tmarathon pace\t50 k\t\t50 k pace' # \t50 mi\t\t50 mi pace'
    print '------------------------------------------------------------------------------------------'
    for m, d, p, hm, tfk, tmi, tk, fk, om, ftk, fmi in dist_mar_pred:
        print '%0.2f' % d, '\t', print_h_m_s(fk), '\t', print_h_m_s(tk), '\t', print_h_m_s(tmi), '\t', print_h_m_s(hm), '\t', print_h_m_s(tfk), '\t', print_h_m_s(m), '\t', print_m_s(m / marathon_distance_mi), '\t\t', print_h_m_s(ftk), '\t', print_m_s(ftk / (50000 / meters_per_mile))
    print ''
    print '%i\t%.4f\t\t%.1f\t\t%.4f\t\t' % (marathon_distance_m, marathon_distance_mi, marathon_distance_m/2., marathon_distance_mi/2.)
    print '%.4f\t%.4f\t\t%.4f\t\t%.4f' % (5000/meters_per_mile, 10000/meters_per_mile, 15000/meters_per_mile, 25000/meters_per_mile)

if __name__ == '__main__':
    do_plot = False

    for arg in os.sys.argv:
        if arg[0:4] == 'plot':
            do_plot = True
    running_pace(do_plot)
