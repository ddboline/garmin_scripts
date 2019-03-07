#!/usr/bin/env python3
import cherrypy
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
from oauthlib.oauth2.rfc6749.errors import MismatchingStateError, MissingTokenError

import matplotlib
matplotlib.use('Agg')
import pylab as pl

#from garmin_app import garmin_utils, garmin_parse, garmin_report
#from garmin_app.util import utc, est

os.set_blocking(0, True)

utc = timezone('UTC')
est = timezone(
    strftime("%Z").replace('CST', 'CST6CDT').replace('EDT', 'EST5EDT'))


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


def get_client(refresh=False):
    if refresh:
        url = 'https://www.ddboline.net/fitbit/auth?%s' % urlencode(
            {
                'id': client_id,
                'secret': client_secret
            })
        webbrowser.open(requests.get(url).text)
        sleep(5)

    user_id, access_token, refresh_token = '', '', ''

    with open('%s/.fitbit_tokens' % os.getenv('HOME'), 'r') as fd:
        for line in fd:
            key, val = line.strip().split('=')
            if key == 'user_id':
                user_id = val
            elif key == 'access_token':
                access_token = val
            elif key == 'refresh_token':
                refresh_token = val

    client = fitbit.Fitbit(
        client_id,
        client_secret,
        access_token=access_token,
        refresh_token=refresh_token)
    try:
        client.user_profile_get()
        return client
    except fitbit.exceptions.HTTPUnauthorized:
        return get_client(refresh=True)
    return client


def get_heartrate_data(begin_date='2017-03-10',
                       end_date=datetime.date.today().isoformat()):
    begin_date = parse(begin_date).date()
    end_date = parse(end_date).date()
    assert end_date >= begin_date
    days = (end_date - begin_date).days
    dates = [begin_date + datetime.timedelta(days=x) for x in range(days + 1)]
    dates = list(map(lambda x: x.isoformat(), dates))

    data = []
    heart_rate_pace_data = []

    client = get_client()
    for date in dates:
        fitbit_hr_data = client.intraday_time_series(
            'activities/heart', base_date=date)
        tmp = fitbit_hr_data['activities-heart-intraday']['dataset']
        tmp = [{
            'time': parse('%sT%s' % (date, x['time'])),
            'value': x['value']
        } for x in tmp]
        print(date, len(tmp))
        data.extend(tmp)

    files = []
    cookies = requests.post(
        f'https://www.ddboline.net/api/auth',
        json={
            'email': garmin_username,
            'password': garmin_password
        }).cookies
    for date in dates:
        js = requests.get(
            f'https://www.ddboline.net/garmin/list_gps_tracks?filter={date}',
            cookies=cookies).json()
        files.extend(js['gps_list'])
    for fname in files:
        print(fname)
        js = requests.get(
            f'https://www.ddboline.net/garmin/get_hr_data?filter={fname}',
            cookies=cookies).json()
        tmp = [{
            'time': parse(x['time']).astimezone(est).isoformat()[:19],
            'value': x['value']
        } for x in js['hr_data']]
        data.extend(tmp)

        js = requests.get(
            f'https://www.ddboline.net/garmin/get_hr_pace?filter={fname}',
            cookies=cookies).json()
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
