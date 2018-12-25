#!/usr/bin/python3
""" fit world record paces to simple model """
from __future__ import (absolute_import, division, print_function, unicode_literals)
import os
import datetime
from dateutil.parser import parse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pl
import pandas as pd
from itertools import chain
from oauth2client.service_account import ServiceAccountCredentials
import gspread

from extract_heartrate_data import get_client

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
        '/home/ddboline/setup_files/build/gapi_scripts/gspread.json',
        ['https://spreadsheets.google.com/feeds'])
    gc = gspread.authorize(credentials)

    def get_spreadsheet_by_title(title, key=None):
        if key:
            s = gc.open_by_key(key)
        else:
            s = gc.open(title)
        w = s.sheet1
        df = pd.DataFrame(w.get_all_records())
        for col in ('Datetime', 'Timestamp'):
            if col in df:
                df[col] = df[col].apply(lambda x: parse(x, ignoretz=True))
        return df

    df = get_spreadsheet_by_title(
        'Scale Measurements', key='1MG8so2pFKoOIpt0Vo9pUAtoNk-Y1SnHq9DiEFi-m5Uw')
    df1 = get_spreadsheet_by_title(
        'Scale Measurement (Responses)', key='1_m-D8U-jHNur6TkpoDufGPn1S9fl_v-_oX_lCnS9LNk')

    df = df.rename(
        columns={
            'Mass': 'mass',
            'Datetime': 'datetime',
            'Fat': 'fat',
            'Water': 'water',
            'Muscle': 'muscle',
            'Bone': 'bone'
        })
    df1 = df1.rename(
        columns={
            'Weight (lbs)': 'mass',
            'Timestamp': 'datetime',
            'Fat %': 'fat',
            'Muscle': 'muscle',
            'Bone': 'bone',
            'Water %': 'water'
        })
    df = df.sort_values(by='datetime')
    df1 = df.sort_values(by='datetime')
    df1 = df1[df1.datetime > df.datetime.max()]
    df = pd.concat([df, df1], axis=0)
    df.index = df.datetime
    df = df.sort_index()

    client = get_client()
    body_weight = {x['date']: x['weight'] for x in client.get_bodyweight(period='30d')['weight']}
    body_fat = {x['date']: x['fat'] for x in client.get_bodyfat(period='30d')['fat']}

    if len(body_weight) == 0 or len(body_fat) == 0:
        min_date = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
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
        cmd = 'mv scale_%s.png /home/ddboline/public_html/' % var
        print(cmd)
        os.system(cmd)
        print('%s\tmean=%s parameters=[%s, %s, %s]' % (var, df[var].mean(), params[0], params[1],
                                                       params[2]))
        print('\t%s +%s -%s' % (v0, vp - v0, v0 - vm))

    df.to_csv('scale_measurements.csv', index=False)

    return


if __name__ == '__main__':
    analyze_scale_measurements()
