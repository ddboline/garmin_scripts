#!/usr/bin/env python3
import os
import sys

import traceback
import webbrowser
import datetime
import requests
import pandas as pd
from dateutil.parser import parse
from urllib.parse import urlencode

from pytz import timezone
from time import strftime, sleep

from base64 import b64encode
import fitbit
from fitbit.api import Fitbit

import matplotlib
matplotlib.use('Agg')
import pylab as pl

#from garmin_app import garmin_utils, garmin_parse, garmin_report
#from garmin_app.util import utc, est

os.set_blocking(0, True)

utc = timezone('UTC')
est = timezone(strftime("%Z").replace('CST', 'CST6CDT').replace('EDT', 'EST5EDT'))


def read_config_env():
    with open('config.env', 'r') as f:
        for l in f:
            (key, val) = l.strip().split('=')[:2]
            os.environ[key] = val


read_config_env()

client_id = os.environ['FITBIT_CLIENTID']
client_secret = os.environ['FITBIT_CLIENTSECRET']
garmin_username = os.environ['GARMIN_USERNAME']
garmin_password = os.environ['GARMIN_PASSWORD']


def get_client(session, refresh=False, tokens_last_mod=None):
    if refresh:
        url = 'https://www.ddboline.net/garmin/fitbit/auth'
        webbrowser.open(session.get(url).text)
        sleep(5)

    token_fname = '%s/.fitbit_tokens' % os.getenv('HOME')
    current_last_mod = None
    if os.path.exists(token_fname):
        current_last_mod = os.stat(token_fname).st_mtime
    else:
        return get_client(session, refresh=True)

    if tokens_last_mod is not None and current_last_mod <= tokens_last_mod:
        sleep(5)
        return get_client(session, refresh=False, tokens_last_mod=tokens_last_mod)

    access_token, refresh_token = '', ''

    with open('%s/.fitbit_tokens' % os.getenv('HOME'), 'r') as fd:
        for line in fd:
            tmp = line.strip().split('=')
            if len(tmp) < 2:
                continue
            key, val = tmp[:2]
            if key == 'access_token':
                access_token = val
            elif key == 'refresh_token':
                refresh_token = val

    client = fitbit.Fitbit(client_id,
                           client_secret,
                           access_token=access_token,
                           refresh_token=refresh_token)
    try:
        client.user_profile_get()
        return client
    except fitbit.exceptions.HTTPUnauthorized:
        if refresh is True:
            return get_client(session, refresh=False, tokens_last_mod=current_last_mod)
        else:
            return get_client(session, refresh=True, tokens_last_mod=current_last_mod)


def get_session():
    session = requests.Session()

    session.post(f'https://www.ddboline.net/api/auth',
                 json={
                     'email': garmin_username,
                     'password': garmin_password
                 })
    return session


def get_heartrate_data(begin_date='2017-03-10', end_date=datetime.date.today().isoformat()):
    begin_date = parse(begin_date).date()
    end_date = parse(end_date).date()
    assert end_date >= begin_date
    days = (end_date - begin_date).days
    dates = [begin_date + datetime.timedelta(days=x) for x in range(days + 1)]
    dates = list(map(lambda x: x.isoformat(), dates))

    data = []
    heart_rate_pace_data = []

    files = []
    session = get_session()

    last_date = dates[0]
    zero_dates = []

    for date in dates:
        url = f'https://www.ddboline.net/garmin/fitbit/heartrate_db?date={date}'
        tmp = session.get(url).json()

        if len(tmp) > 0:
            last_date = date
        else:
            zero_dates.append(date)
        tmp = [{'time': parse(x['datetime']).astimezone(est).isoformat()[:19], 'value': x['value']} for x in tmp]
        print(date, len(tmp))
        data.extend(tmp)

    for date in [last_date] + zero_dates:
        url = f'https://www.ddboline.net/garmin/fitbit/sync?date={date}'
        session.get(url).raise_for_status()
        print(f'sync {date}')

    for date in dates:
        js = session.get(f'https://www.ddboline.net/garmin/list_gps_tracks?filter={date}').json()
        files.extend(js['gps_list'])
    for fname in files:
        print(fname)
        js = session.get(f'https://www.ddboline.net/garmin/get_hr_data?filter={fname}').json()
        tmp = [{
            'time': parse(x['time']).astimezone(est).isoformat()[:19],
            'value': x['value']
        } for x in js['hr_data']]
        data.extend(tmp)

        js = session.get(f'https://www.ddboline.net/garmin/get_hr_pace?filter={fname}').json()
        tmp = [{'hrt': int(x['hr']), 'pace': x['pace']} for x in js['hr_pace']]
        heart_rate_pace_data.extend(tmp)
    df = pd.DataFrame(data)
    if df.shape[0] > 0:
        df.index = pd.to_datetime(df.time)
        ts = df.sort_index().value
        pl.clf()
        ts.resample('5Min').mean().dropna().plot()
        pl.savefig('heartrate_data.png')
        os.system('mv heartrate_data.png /home/ddboline/public_html/')

    df = pd.DataFrame(heart_rate_pace_data)
    if df.shape[0] > 0:
        pl.clf()
        #df.plot.scatter('hrt', 'pace')
        df.plot.hexbin('hrt', 'pace', gridsize=30)
        pl.savefig('hrt_vs_pace.png')
        os.system('mv hrt_vs_pace.png /home/ddboline/public_html/')

    for f in ('hrt_vs_pace.png', 'heartrate_data.png'):
        cmd = 'scp /home/ddboline/public_html/%s ubuntu@cloud.ddboline.net:~/public_html/' % f
        os.system(cmd)

    return df


if __name__ == '__main__':
    begin_date, end_date = None, None
    for arg in os.sys.argv:
        if begin_date is None:
            try:
                begin_date = parse(arg).date()
            except:
                pass
        elif end_date is None:
            try:
                end_date = parse(arg).date()
            except:
                pass
    if begin_date is None:
        begin_date = datetime.date.today() - datetime.timedelta(days=3)
    if end_date is None:
        end_date = datetime.date.today()
    x = get_heartrate_data(begin_date.isoformat(), end_date.isoformat())
