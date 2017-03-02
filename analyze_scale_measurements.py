#!/usr/bin/python
""" fit world record paces to simple model """
from __future__ import (absolute_import, division, print_function, unicode_literals)
import os
import datetime
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pl
import pandas as pd
from itertools import chain
from oauth2client.service_account import ServiceAccountCredentials
import gspread

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

try:
    from world_record import do_fit
except ImportError:
    os.sys.path.append('%s' % os.getenv('HOME'))
    from scripts.world_record import do_fit


def analyze_scale_measurements():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        '/home/ddboline/setup_files/build/gapi_scripts/gspread.json', ['https://spreadsheets.google.com/feeds'])
    gc = gspread.authorize(credentials)

    def get_spreadsheet_by_title(title):
        s = gc.open(title)
        w = s.sheet1
        o = w.export()
        return pd.read_csv(StringIO(o), parse_dates=[0])

    df = get_spreadsheet_by_title('Scale Measurements')
    df1 = get_spreadsheet_by_title('Scale Measurement (Responses)')

    df = df.rename(columns={
        'Mass': 'mass',
        'Datetime': 'datetime',
        'Fat': 'fat',
        'Water': 'water',
        'Muscle': 'muscle',
        'Bone': 'bone'
    })
    df1 = df1.rename(columns={
        'Weight (lbs)': 'mass',
        'Timestamp': 'datetime',
        'Fat %': 'fat',
        'Muscle': 'muscle',
        'Bone': 'bone',
        'Water %': 'water'
    })
    df1 = df1[df1.datetime > df.datetime.max()]
    df = pd.concat([df, df1], axis=0)
    df.index = df.datetime
    df = df.sort_index()
    print(df)
    df['days'] = (df.datetime - df.datetime[0]).apply(lambda x: x.days)
    today = (datetime.datetime.now() - df.datetime[0]).days
    xval = np.linspace(0, df['days'].max())

    tmp = pd.Series(np.arange(0, df['days'].max()))
    tmp = tmp.apply(lambda x: df.datetime[0] + datetime.timedelta(days=x))
    xtickarray = tmp[tmp.dt.day == 1].index
    xticklabels = range(len(xtickarray))

    def lin_func(xval, *params):
        return sum(params[i] * xval**i for i in range(5))

    for var in ('mass', 'fat', 'water', 'muscle', 'bone'):
        min_, max_ = df[var].min(), df[var].max()
        margin = (max_ - min_) * 0.05
        ytickarray = np.linspace(min_ - margin, max_ + margin, 10)
        yticklabels = ['%3.1f' % x for x in ytickarray]

        data = df[['days', var]].values
        params, dparams = do_fit(data, lin_func, param_default=[75, 1, 1, 1, 1])
        pp_, pm_ = params + dparams, params - dparams

        v0 = lin_func(today, *params)
        vp = lin_func(today, *pp_)
        vm = lin_func(today, *pm_)

        pl.clf()
        pl.plot(df['days'], df[var])
        pl.plot(xval, lin_func(xval, *params), 'b')

        pl.plot(xval, lin_func(xval, *params), 'b', linewidth=2.5)
        #        pl.plot(xval, lin_func(xval, *pp_), 'b--')
        #        pl.plot(xval, lin_func(xval, *pm_), 'b--')

        pl.xticks(xtickarray, xticklabels)
        pl.yticks(ytickarray, yticklabels)
        pl.title(var)
        pl.xlabel('months')
        if var == 'mass':
            pl.ylabel('lbs')
        else:
            pl.ylabel('%')
        pl.savefig('scale_%s.png' % var)
        os.system('mv scale_%s.png /home/ddboline/public_html/' % var)
        print('%s\tmean=%s parameters=[%s, %s, %s]' %
              (var, df[var].mean(), params[0], params[1], params[2]))
        print('\t%s +%s -%s' % (v0, vp - v0, v0 - vm))

    return


if __name__ == '__main__':
    analyze_scale_measurements()
