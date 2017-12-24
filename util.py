#!/usr/bin/python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from subprocess import call, Popen, PIPE

HOMEDIR = os.getenv('HOME')


class PopenWrapperClass(object):
    """ context wrapper around subprocess.Popen """

    def __init__(self, command):
        """ init fn """
        self.command = command
        self.pop_ = Popen(self.command, shell=True, stdout=PIPE)

    def __iter__(self):
        return self.pop_.stdout

    def __enter__(self):
        """ enter fn """
        return self.pop_.stdout

    def __exit__(self, exc_type, exc_value, traceback):
        """ exit fn """
        if hasattr(self.pop_, '__exit__'):
            efunc = getattr(self.pop_, '__exit__')
            return efunc(exc_type, exc_value, traceback)
        else:
            self.pop_.wait()
            if exc_type or exc_value or traceback:
                return False
            else:
                return True


def run_command(command, do_popen=False, turn_on_commands=True, single_line=False):
    """ wrapper around os.system """
    if not turn_on_commands:
        print(command)
        return command
    elif do_popen:
        if single_line:
            with PopenWrapperClass(command) as pop_:
                return pop_.read()
        else:
            return PopenWrapperClass(command)
    else:
        return call(command, shell=True)


def convert_date(input_date):
    import datetime
    _month = int(input_date[0:2])
    _day = int(input_date[2:4])
    _year = 2000 + int(input_date[4:6])
    return datetime.date(_year, _month, _day)


def print_h_m_s(second):
    ''' convert time from seconds to hh:mm:ss format '''
    hours = int(second / 3600)
    minutes = int(second / 60) - hours * 60
    seconds = int(second) - minutes * 60 - hours * 3600
    return '%02i:%02i:%02i' % (hours, minutes, seconds)


def print_m_s(second):
    ''' convert time from seconds to mm:ss format '''
    hours = int(second / 3600)
    minutes = int(second / 60) - hours * 60
    seconds = int(second) - minutes * 60 - hours * 3600
    if hours == 0:
        return '%02i:%02i' % (minutes, seconds)
    else:
        return '%02i:%02i:%02i' % (hours, minutes, seconds)


def datetimefromstring(tstr, ignore_tz=False):
    from dateutil.parser import parse
    return parse(tstr, ignoretz=ignore_tz)


def test_run_command():
    cmd = 'echo "HELLO"'
    out = run_command(cmd, do_popen=True, single_line=True).strip()
    print(out, cmd)
    assert out == b'HELLO'


def test_datetimefromstring():
    import datetime
    from pytz import UTC
    dt0 = '1980-11-17T05:12:13Z'
    dt1 = datetime.datetime(year=1980, month=11, day=17, hour=5, minute=12, second=13, tzinfo=UTC)
    assert datetimefromstring(dt0) == dt1
