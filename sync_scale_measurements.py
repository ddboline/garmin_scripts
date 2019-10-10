#!/usr/bin/python3
import requests
import os
import datetime


def read_config_env():
    homedir = os.environ.get('HOME', '/tmp')
    with open(f'{homedir}/setup_files/build/garmin_scripts/config.env',
              'r') as f:
        for l in f:
            (key, val) = l.strip().split('=')[:2]
            os.environ[key] = val


read_config_env()

garmin_username = os.environ['GARMIN_USERNAME']
garmin_password = os.environ['GARMIN_PASSWORD']

entry_map = {
    'imdb_episodes': 'episodes',
    'imdb_ratings': 'shows',
    'movie_collection': 'collection',
    'movie_queue': 'queue'
}

dry_run = False


def get_json(url, cookies, retry=5):
    result = requests.get(url, cookies=cookies)
    print(result)
    if result.status_code != 200:
        return get_json(url, cookies, retry - 1)
    return result.json()


def sync_scale_measurements(path='/garmin/scale_measurements', js_prefix='measurements'):
    from_endpoint = 'https://cloud.ddboline.net'
    to_endpoint = 'https://www.ddboline.net'

    cookies0 = requests.post(f'{from_endpoint}/api/auth',
                             json={
                                 'email': garmin_username,
                                 'password': garmin_password
                             }).cookies
    cookies1 = requests.post(f'{to_endpoint}/api/auth',
                             json={
                                 'email': garmin_username,
                                 'password': garmin_password
                             }).cookies

    print(f'{from_endpoint}{path}')

    measurements0 = get_json(f'{from_endpoint}{path}', cookies=cookies0)
    print(f'{to_endpoint}{path}')
    measurements1 = get_json(f'{to_endpoint}{path}', cookies=cookies1)
    measurements0 = {x['datetime']: x for x in measurements0}
    measurements1 = {x['datetime']: x for x in measurements1}

    measurements = [
        measurements0[x] for x in (set(measurements0) - set(measurements1))
    ]
    if len(measurements) > 0:
        if len(measurements) < 20:
            print(measurements)
        else:
            print(len(measurements))
        requests.post(f'{to_endpoint}{path}', cookies=cookies1, json={js_prefix: measurements})
    measurements = [measurements1[x] for x in (set(measurements1) - set(measurements0))]
    if len(measurements) > 0:
        if len(measurements) < 20:
            print(measurements)
        else:
            print(len(measurements))
        requests.post(f'{from_endpoint}{path}', cookies=cookies0, json={js_prefix: measurements})
    return


if __name__ == '__main__':
    sync_scale_measurements()
    dates = [datetime.date.today() - datetime.timedelta(days=i) for i in range(10)]
    for date in dates:
        sync_scale_measurements(path=f'/garmin/fitbit/heartrate_db?date={date}',
                                js_prefix='updates')
