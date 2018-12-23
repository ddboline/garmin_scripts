#!/usr/bin/env python3
import cherrypy
import os
import sys
import threading
import traceback
import webbrowser
import datetime
import requests
import pandas as pd
from dateutil.parser import parse

from pytz import timezone
from time import strftime

from base64 import b64encode
import fitbit
from fitbit.api import Fitbit
from oauthlib.oauth2.rfc6749.errors import MismatchingStateError, MissingTokenError

import matplotlib
matplotlib.use('Agg')
import pylab as pl

#from garmin_app import garmin_utils, garmin_parse, garmin_report
#from garmin_app.util import utc, est

utc = timezone('UTC')
est = timezone(strftime("%Z").replace('CST', 'CST6CDT').replace('EDT', 'EST5EDT'))

client_id = '228D9P'
client_secret = '9d7aa34320fac07106dca853dab8603d'


class OAuth2Server:

    def __init__(self, client_id, client_secret, redirect_uri='http://127.0.0.1:8080/'):
        """ Initialize the FitbitOauth2Client """
        self.success_html = """
            <h1>You are now authorized to access the Fitbit API!</h1>
            <br/><h3>You can close this window</h3>"""
        self.failure_html = """
            <h1>ERROR: %s</h1><br/><h3>You can close this window</h3>%s"""

        self.fitbit = fitbit.Fitbit(
            client_id,
            client_secret,
            redirect_uri=redirect_uri,
            timeout=10,
        )

    def browser_authorize(self):
        """
        Open a browser to the authorization url and spool up a CherryPy
        server to accept the response
        """
        url, _ = self.fitbit.client.authorize_token_url()
        # Open the web browser in a new thread for command-line browser support
        threading.Timer(1, webbrowser.open, args=(url, )).start()
        cherrypy.quickstart(self)

    @cherrypy.expose
    def index(self, state, code=None, error=None):
        """
        Receive a Fitbit response containing a verification code. Use the code
        to fetch the access_token.
        """
        error = None
        if code:
            try:
                self.fitbit.client.fetch_access_token(code)
            except MissingTokenError:
                error = self._fmt_failure('Missing access token parameter.</br>Please check that '
                                          'you are using the correct client_secret')
            except MismatchingStateError:
                error = self._fmt_failure('CSRF Warning! Mismatching state')
        else:
            error = self._fmt_failure('Unknown error while authenticating')
        # Use a thread to shutdown cherrypy so we can return HTML first
        self._shutdown_cherrypy()
        return error if error else self.success_html

    def _fmt_failure(self, message):
        tb = traceback.format_tb(sys.exc_info()[2])
        tb_html = '<pre>%s</pre>' % ('\n'.join(tb)) if tb else ''
        return self.failure_html % (message, tb_html)

    def _shutdown_cherrypy(self):
        """ Shutdown cherrypy in one second, if it's running """
        if cherrypy.engine.state == cherrypy.engine.states.STARTED:
            threading.Timer(1, cherrypy.engine.exit).start()


def get_client(refresh=False):
    if refresh:
        server = OAuth2Server(client_id, client_secret)
        server.browser_authorize()
        access_token = server.fitbit.client.session.token['access_token']
        refresh_token = server.fitbit.client.session.token['refresh_token']
        user_id = server.fitbit.client.session.token['user_id']
        with open('%s/.fitbit_tokens' % os.getenv('HOME'), 'w') as fd:
            fd.write('user_id=%s\n' % user_id)
            fd.write('access_token=%s\n' % access_token)
            fd.write('refresh_token=%s\n' % refresh_token)
    else:
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
        client_id, client_secret, access_token=access_token, refresh_token=refresh_token)
    try:
        client.user_profile_get()
        return client
    except fitbit.exceptions.HTTPUnauthorized:
        return get_client(refresh=True)
    return client


def get_heartrate_data(begin_date='2017-03-10', end_date=datetime.date.today().isoformat()):
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
        fitbit_hr_data = client.intraday_time_series('activities/heart', base_date=date)
        tmp = fitbit_hr_data['activities-heart-intraday']['dataset']
        tmp = [{'time': parse('%sT%s' % (date, x['time'])), 'value': x['value']} for x in tmp]
        data.extend(tmp)

    files = []
    for date in dates:
        js = requests.get(f'https://www.ddboline.net/garmin/list_gps_tracks?filter={date}').json()
        files.extend(js['gps_list'])
    for fname in files:
        js = requests.get(f'https://www.ddboline.net/garmin/get_hr_data?filter={fname}').json()
        tmp = [{
            'time': parse(x['time']).astimezone(est).isoformat()[:19],
            'value': x['value']
        } for x in js['hr_data']]
        data.extend(tmp)

        js = requests.get(f'https://www.ddboline.net/garmin/get_hr_pace?filter={fname}').json()
        tmp = [{'hrt': int(x['hr']), 'pace': x['pace']} for x in js['hr_pace']]
        heart_rate_pace_data.extend(tmp)
    df = pd.DataFrame(data)
    if df.shape[0] > 0:
        df.index = df.time
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
