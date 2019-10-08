#!/usr/bin/python3
""" fit world record paces to simple model """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import datetime
from dateutil.parser import parse
from dateutil.tz import tzutc
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pl
import pandas as pd
from itertools import chain

from extract_heartrate_data import get_client, get_session, DEFAULT_HOST

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

try:
    from world_record import do_fit
except ImportError:
    os.sys.path.append('%s' % os.getenv('HOME'))
    from scripts.world_record import do_fit

os.set_blocking(0, True)
HOME = os.environ['HOME']


def analyze_scale_measurements(host=DEFAULT_HOST):
    session = get_session()
    url = f'https://{host}/garmin/scale_measurements'
    js = session.get(url).json()
    df = pd.DataFrame(js)
    df['datetime'] = df['datetime'].apply(lambda x: parse(x))

    df = df.rename(
        columns={
            'mass': 'mass',
            'datetime': 'datetime',
            'fat_pct': 'fat',
            'water_pct': 'water',
            'muscle_pct': 'muscle',
            'bone_pct': 'bone'
        })
    df = df.sort_values(by='datetime')
    df.index = df.datetime
    df = df.sort_index()

    client = get_client(session)
    body_weight = {
        x['date']: x['weight']
        for x in client.get_bodyweight(period='30d')['weight']
    }
    body_fat = {
        x['date']: x['fat']
        for x in client.get_bodyfat(period='30d')['fat']
    }

    if len(body_weight) == 0 or len(body_fat) == 0:
        min_date = (datetime.date.today() -
                    datetime.timedelta(days=30)).isoformat()
    else:
        min_date = min(chain(body_weight.keys(), body_fat.keys()))
    cond = df.datetime.dt.date >= parse(min_date).date()
    for idx, row in df[cond].iterrows():
        date = row['datetime'].date().isoformat()
        time = row['datetime'].time().strftime('%H:%M:%S')
        mass = row['mass']
        fat = row['fat']
        if date not in body_weight:
            url = 'https://api.fitbit.com/1/user/-/body/log/weight.json'
            data = {'date': date, 'time': time, 'weight': mass}
            print(url)
            client.make_request(url, data=data, method='POST')
        if date not in body_fat:
            url = 'https://api.fitbit.com/1/user/-/body/log/fat.json'
            data = {'date': date, 'time': time, 'fat': fat}
            print(url)
            client.make_request(url, data=data, method='POST')
    df['days'] = (df.datetime - df.datetime[0]).apply(lambda x: x.days)
    today = (datetime.datetime.now(tzutc()) - df.datetime[0]).days
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
        params, dparams = do_fit(data,
                                 lin_func,
                                 param_default=[75, 1, 1, 1, 1])
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
        pl.savefig(f'scale_{var}.png')
        cmd = f'mv scale_{var}.png {HOME}/public_html/'
        print(cmd)
        os.system(cmd)
        print('%s\tmean=%s parameters=[%s, %s, %s]' %
              (var, df[var].mean(), params[0], params[1], params[2]))
        print('\t%s +%s -%s' % (v0, vp - v0, v0 - vm))

    df.to_csv('scale_measurements.csv', index=False)

    if DEFAULT_HOST != 'www.ddboline.net':
        return

    for var in ('mass', 'fat', 'water', 'muscle', 'bone'):
        cmd = f'scp {HOME}/public_html/scale_{var}.png ubuntu@cloud.ddboline.net:~/public_html/'
        os.system(cmd)

    return


if __name__ == '__main__':
    analyze_scale_measurements()
