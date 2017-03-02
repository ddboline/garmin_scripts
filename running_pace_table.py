#!/usr/bin/python
from __future__ import (absolute_import, division, print_function, unicode_literals)
import os
from util import print_h_m_s, print_m_s

HOMEDIR = os.getenv('HOME')

paces = []


def print_time(pace, dist):
    """ format time """
    print(print_m_s(pace), print_h_m_s(dist * pace))


def print_time_a_b_c_d_e_f(dist_a, pace_a, dist_b, pace_b, dist_c, pace_c, dist_d, pace_d, dist_e,
                           pace_e, dist_f, pace_f):
    """ format table """
    print('\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' %
          (print_m_s(pace_a), print_h_m_s(dist_a * pace_a), print_m_s(pace_b),
           print_h_m_s(dist_b * pace_b), print_m_s(pace_c), print_h_m_s(dist_c * pace_c),
           print_m_s(pace_d), print_h_m_s(dist_d * pace_d), print_m_s(pace_e),
           print_h_m_s(dist_e * pace_e), print_m_s(pace_f), print_h_m_s(dist_f * pace_f)))


def running_pace():
    print('pace \t\t 400m \t 800m \t 1200m \t 4mi \t\t 5mi \t\t 8mi \t\t ' +
          'half_marathon \t marathon \t 50mi')
    print('---------------------------------------------------------------' +
          '-------------------------------------------')

    meters_per_mile = 1609.344  # meters
    km_per_mile = meters_per_mile / 1000
    marathon_distance_m = 42195  # meters
    marathon_distance_mi = marathon_distance_m / meters_per_mile  # meters
    pace_every_two_miles = []
    pace_every_five_k = []
    for mi in range(10, 26, 2):
        pace_every_two_miles.append([mi, ''])
    for km in [x for x in range(5, 35, 5)] + [50] + [80]:
        mi = km / km_per_mile
        pace_every_five_k.append([mi, ''])

    pace_every_five_k_later = []
    for km in range(35, 75, 5):
        mi = km / km_per_mile
        pace_every_five_k_later.append([mi, ''])

    for second in range(4 * 60 + 50, 15 * 60, 10):
        pace = print_h_m_s(second)
        four_hundred_meter = print_m_s(second * 400 / meters_per_mile)
        eight_hundred_meter = print_m_s(second * 800 / meters_per_mile)
        twelve_hundred_meter = print_m_s(second * 1200 / meters_per_mile)
        marathon = print_h_m_s(marathon_distance_mi * second)
        half_marathon = print_h_m_s(marathon_distance_mi / 2. * second)
        #        ten_mile = print_h_m_s(10 * second)
        #        ten_k = print_h_m_s(10/km_per_mile * second)
        four_mi = print_h_m_s(4 * second)
        five_mi = print_h_m_s(5 * second)
        eight_mi = print_h_m_s(8 * second)
        #        five_k = print_h_m_s(5/km_per_mile * second)
        fifty_mi = print_h_m_s(50 * second)
        print('%s \t %s \t %s \t %s \t %s \t %s \t %s \t %s \t %s \t %s' %
              (pace, four_hundred_meter, eight_hundred_meter, twelve_hundred_meter, four_mi,
               five_mi, eight_mi, half_marathon, marathon, fifty_mi))

    print('\n\n')

    print('pace \t\t 10mi \t\t 12mi \t\t 14mi \t\t 16mi \t\t 18mi \t\t 20mi ' +
          '\t\t 22mi \t\t 24mi')
    print('-----------------------------------------------------------------' +
          '-------------------------')

    for second in range(4 * 60 + 50, 19 * 60, 10):
        pace = print_h_m_s(second)
        output_ = ['%s \t' % pace]
        for idx in range(0, len(pace_every_two_miles)):
            pace_every_two_miles[idx][1] = print_h_m_s(pace_every_two_miles[idx][0] * second)
            output_.append('%s \t' % pace_every_two_miles[idx][1])
        print(''.join(output_))

    print('\n\n')

    print('pace \t\t 5km \t\t 10km \t\t 15km \t\t 20km \t\t 25km \t\t 30km ' +
          '\t\t 50km \t\t 80km')
    print('----------------------------------------------------------------' +
          '--------------------------')
    for second in range(4 * 60 + 50, 15 * 60, 10):
        pace = print_h_m_s(second)
        output_ = ['%s \t' % pace]
        for idx in range(0, len(pace_every_five_k)):
            pace_every_five_k[idx][1] = print_h_m_s(pace_every_five_k[idx][0] * second)
            output_.append('%s \t' % pace_every_five_k[idx][1])
        print(''.join(output_))

    print('\n\n')

    print('pace \t\t 35km \t\t 40km \t\t 45km \t\t 50km \t\t 55km \t\t 60km ' +
          '\t\t 65km \t\t 80km')
    print('-----------------------------------------------------------------' +
          '-------------------------')
    for second in range(4 * 60 + 50, 16 * 60, 10):
        pace = print_h_m_s(second)
        output_ = ['%s \t' % pace]
        for idx in range(0, len(pace_every_five_k_later)):
            pace_every_five_k_later[idx][1] = print_h_m_s(pace_every_five_k_later[idx][0] * second)
            output_.append('%s \t' % pace_every_five_k_later[idx][1])
        print(''.join(output_))

    print('\n\n')

    # greenbelt_legs = (3.3, 2.9, 2.8, 2.8, 2.9, 2.9, 2.9, 2.8, 2.8, 2.9, 2.9)
    # o2s50_legs = (6.0, 6.0, 6.3, 5.8, 6.2, 5.4, 7, 6.4)
    # jfk50_legs = (2.5, 6.8, 6.2, 11.6, 7.3, 4, 3.4, 4.2, 4.2)
    # rocky_100_legs = (3.10, 2.64, 6.95, 2.96, 4.36)
    # rocky_100_legs = tuple(sum(rocky_100_legs) for _ in range(5))

    paumanok_pursuit_legs = (10.75, 8.5, 10.0, 7.5, 6.75)
    nfecdc_legs = (2.1, 3.5, 2.7, 4.8, 4.1, 1.8, 4.8, 2.7, 3.5, 1.7)
    bear_mountain_legs = (4.0, 4.7, 5.5, 4.3, 2.7, 4.4, 2.5, 2.8)
    #bear_mountain_legs = (4.0, 4.7, 5.5, 5.6, 3.4, 5.8, 6.2, 3.4, 2.7, 4.4, 2.5, 2.8)
    tesla_100_legs = tuple(10.4 for _ in range(10))
    superior_100_legs = (9.7, 10.4, 4.9, 9.9, 8.6, 7.7, 7.5, 4.2, 9.4, 5.6, 7.1, 5.7, 5.5, 7.1)

    def cumulative_table(label, leg_distances, min_pace=6, max_pace=17):
        cumulative_distances = tuple(sum(leg_distances[:i + 1]) for i in range(len(leg_distances)))
        print('%s Cumulative Time' % label)
        output = '%10s' % ''
        for dist in leg_distances:
            output += '%6s%4s' % ('%0.1fmi' % dist, '')
        print(output)
        output = 'pace%6s' % ''
        for dist in cumulative_distances:
            output += '%6s%4s' % ('%0.1fmi' % dist, '')
        print(output)
        for a in range(0, 120):
            os.sys.stdout.write('-')
            os.sys.stdout.flush()
        print('')
        for second in range(min_pace * 60, max_pace * 60, 10):
            pace = print_h_m_s(second)
            output = '%8s%2s' % (pace, '')
            for cum_dist in cumulative_distances:
                outstr = print_h_m_s(cum_dist * second)
                output += '%8s  ' % outstr
            print(output)
        print('\n\n')

    #cumulative_table('Bear Mountain 50mi', bear_mountain_legs)
    cumulative_table('Paumanok Pursuit', paumanok_pursuit_legs, min_pace=9, max_pace=14)
    # cumulative_table('Rocky Raccoon 100 mi', rocky_100_legs)
    # cumulative_table('Tesla 100 mi', tesla_100_legs)
    #cumulative_table('North Face DC', nfecdc_legs)
    #cumulative_table('Superior 100mi', superior_100_legs)


if __name__ == '__main__':
    running_pace()
