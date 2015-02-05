#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os, glob
import datetime
from garmin_base import garmin_file, do_summary, METERS_PER_MILE, SPORT_TYPES,\
    convert_gmn_to_gpx, do_plots, print_file_string, print_splits
from util import run_command
import multiprocessing
import socket

#BASEURL = 'https://ddbolineathome.mooo.com/~ddboline'
BASEURL = 'http://ddbolineinthecloud.mooo.com/~ubuntu'

GARMIN_SOCKET_FILE = '/tmp/.garmin_test_socket'

def server_thread(socketfile=GARMIN_SOCKET_FILE, msg_q=None):
    '''
        server_thread, listens for commands, sends back responses.
    '''
    script_path = '/'.join(os.path.abspath(os.sys.argv[0]).split('/')[:-1])
    
    if os.path.exists(socketfile):
        os.remove(socketfile)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.bind(socketfile)
        os.chmod(socketfile, 0o777)
    except socket.error:
        time.sleep(10)
        print('try again to open socket')
        return server_thread(socketfile, msg_q)
    print('socket open')
    s.listen(0)

    net_pid = -1
    while True:
        outstring = []
        c, a = s.accept()
        d = c.recv(1024)

        args = d.split()
        
        gdir = []
        options = {'do_plot': False, 'do_year': False, 'do_month': False, 'do_week': False, 'do_day': False, 'do_file': False, 'do_sport': None, 'do_update': False, 'do_average': False}
        options['script_path'] = script_path
        for arg in args:
            if arg == 'build':
                options['build'] = True
            elif arg == 'backup':
                fname = '%s/garmin_data_%s.tar.gz' % (script_path, datetime.date.today().strftime('%Y%m%d'))
                run_command('cd %s/run/ ; tar zcvf %s 2* garmin.pkl' % (script_path, fname))
                if os.path.exists('%s/public_html/backup' % os.getenv('HOME')):
                    run_command('cp %s %s/public_html/backup/garmin_data.tar.gz' % (fname, os.getenv('HOME')))
                if os.path.exists('%s/public_html/garmin/tar' % os.getenv('HOME')):
                    run_command('mv %s %s/public_html/garmin/tar' % (fname, os.getenv('HOME')))
            elif arg == 'occur':
                options['occur'] = True
            elif os.path.isfile(arg):
                gdir.append(arg)
            elif arg != 'run' and os.path.isdir(arg):
                gdir.append(arg)
            elif arg != 'run' and os.path.isdir('%s/run/%s' % (script_path, arg)):
                gdir.append('%s/run/%s' % (script_path, arg))
            elif arg in options:
                options[arg] = True
            elif 'do_%s' % arg in options:
                options['do_%s' % arg] = True
            else:
                spts = filter(lambda x: arg in x, list(SPORT_TYPES))
                if len(spts) > 0:
                    options['do_sport'] = spts[0]
                elif arg == 'bike':
                    options['do_sport'] = 'biking'
                elif '-' in arg:
                    ent = arg.split('-')
                    year = ent[0]
                    if len(ent) > 1:
                        month = ent[1]
                    else:
                        month = '*'
                    files = glob.glob('%s/run/%s/%s/%s*' % (script_path, year, month, arg)) + glob.glob('%s/run/%s/%s/%s*' % (script_path, year, month, ''.join(ent)))
                    basenames = [f.split('/')[-1] for f in sorted(files)]
                    if len(filter(lambda x: x[:10] == basenames[0][:10], basenames)) == len(basenames):
                        for f in basenames:
                            print(f)
                    gdir += files
                elif '.gmn' in arg or 'T' in arg:
                    files = glob.glob('%s/run/*/*/%s' % (script_path, arg))
                    gdir += files
                else:
                    print('unhandled argument:',arg)
        if not gdir:
            gdir.append('%s/run' % script_path)
        if len(gdir) == 1 and os.path.isfile(gdir[0]):
            read_garmin_file(gdir[0], **options)
        else:
            do_summary(gdir, **options)
        c.send('done')
        c.close()
    s.shutdown(socket.SHUT_RDWR)
    s.close()
    return 0



def read_garmin_file(fname, **options):
    gfile = garmin_file(fname)

    print(print_file_string(gfile))
    if gfile.is_txt:
        return
    print('')
    print(print_splits(gfile, METERS_PER_MILE))
    print('')
    print(print_splits(gfile, 5000., 'km'))

    avg_hr = 0
    sum_time = 0
    hr_vals = []
    for point in gfile.points:
        if point.heart_rate > 0:
            avg_hr += point.heart_rate * point.duration_from_last
            sum_time += point.duration_from_last
            hr_vals.append(point.heart_rate)
    if sum_time > 0:
        avg_hr /= sum_time
        if len(hr_vals) > 0:
            print('Heart Rate %2.2f avg %2.2f max' % (avg_hr, max(hr_vals)))

    alt_vals = []
    vertical_climb = 0
    for point in gfile.points:
        if point.altitude > 0:
            alt_vals.append(point.altitude)
            if len(alt_vals) > 1 and alt_vals[-1] > alt_vals[-2]:
                vertical_climb += alt_vals[-1] - alt_vals[-2]
    if len(alt_vals) > 0:
        print('max altitude diff: %.2f m' % (max(alt_vals) - min(alt_vals)))
        print('vertical climb: %.2f m' % vertical_climb)
    print('')

    gpx_filename = convert_gmn_to_gpx(fname)
    do_plots(gfile, **options)


if __name__ == '__main__':
    msg_q = multiprocessing.Queue()
    
    net = multiprocessing.Process(target=server_thread, args=(GARMIN_SOCKET_FILE, msg_q))
    net.start()
    
    net.join()
