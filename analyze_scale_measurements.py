#!/usr/bin/python
""" fit world record paces to simple model """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import datetime
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pl
import pandas as pd
#import scipy.optimize as optimize
from itertools import chain
try:
    from world_record import do_fit
except ImportError:
    os.sys.path.append('%s' % os.getenv('HOME'))
    from scripts.world_record import do_fit


def analyze_scale_measurements():
    fname = '/home/ddboline/gDrive/Scale Measurements'
    fname1 = '/home/ddboline/gDrive/Scale Measurement (Responses)'
    df = pd.read_excel(fname, index=None)
    df1 = pd.read_excel(fname1, index=None)

    df = df.rename(columns={'Mass': 'mass', 'Datetime': 'datetime',
                            'Fat': 'fat', 'Water': 'water', 'Muscle': 'muscle',
                            'Bone': 'bone'})
    df1 = df1.rename(columns={'Weight (lbs)': 'mass', 'Timestamp': 'datetime',
                              'Fat %': 'fat', 'Muscle': 'muscle',
                              'Bone': 'bone', 'Water %': 'water'})
    rows = {}
    for idx, row in chain(*[x.iterrows() for x in (df, df1)]):
        dt = row['datetime']
        if dt not in rows:
            rows[dt] = row.to_dict()
    df = pd.DataFrame(rows.values(),
                      columns=['datetime', 'mass', 'fat', 'water', 'muscle',
                               'bone']).sort_values(by=['datetime'])
    df.index = np.arange(df.shape[0])
    print(df)
    df['days'] = (df.datetime - df.datetime[0]).apply(lambda x: x.days)
    today = (datetime.datetime.now() - df.datetime[0]).days
    xval = np.linspace(0, max(df['days']))

    def lin_func(xval, *params):
        return params[0] + xval * params[1] + xval**2 * params[2]

    for var in ('mass', 'fat', 'water', 'muscle', 'bone'):
        data = df[['days', var]].values
        params, dparams = do_fit(data, lin_func, param_default=[75, 1, 1])
        pp_, pm_ = params+dparams, params-dparams

        v0 = lin_func(today, *params)
        vp = lin_func(today, *pp_)
        vm = lin_func(today, *pm_)

        pl.clf()
        pl.plot(df['days'], df[var])
        pl.plot(xval, lin_func(xval, *params), 'b')

        pl.plot(xval, lin_func(xval, *params), 'b', linewidth=2.5)
        pl.plot(xval, lin_func(xval, *pp_), 'b--')
        pl.plot(xval, lin_func(xval, *pm_), 'b--')

        pl.title(var)
        pl.xlabel('days')
        if var == 'mass':
            pl.ylabel('lbs')
        else:
            pl.ylabel('%')
        pl.savefig('scale_%s.png' % var)
        os.system('mv scale_%s.png /home/ddboline/public_html/' % var)
        print('%s\tmean=%s parameters=[%s, %s, %s]' % (var, df[var].mean(), params[0], params[1], params[2]))
        print('\t%s +%s -%s' % (v0, vp-v0, v0-vm))

    return

if __name__ == '__main__':
    analyze_scale_measurements()
