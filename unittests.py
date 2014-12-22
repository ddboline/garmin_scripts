#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Unit testing testing...
"""

import unittest
import datetime

import garmin_base
from util import run_command

class TestGarminScript(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_garmin_base(self):
        gmnfile = 'run/2011/05/20110507T144308.gmn'
        tcxfile = 'run/2012/11/2012-11-05-065221.TCX'
        fitfile = 'run/2014/01/2014-01-12_11-30-08-80-7743.fit'
        txtfile = 'run/2013/01/20130116_ellip.txt'

        outfile = garmin_base.convert_gmn_to_gpx(gmnfile)
        self.assertEqual('/tmp/temp.gpx', outfile)
        md5 = run_command('tail -n186 %s | md5sum' % outfile, do_popen=True).read().split()[0]
        self.assertEqual(md5, '93e68a7fcc0e6b41037e16d3f3c59baa')

        outfile = garmin_base.convert_gmn_to_gpx(tcxfile)
        self.assertEqual('/tmp/temp.gpx', outfile)
        md5 = run_command('tail -n740 %s | md5sum' % outfile, do_popen=True).read().split()[0]
        self.assertEqual(md5, '3e7ab7d5dc77a6e299596d615226ff0b')

        outfile = garmin_base.convert_gmn_to_gpx(fitfile)
        self.assertEqual('/tmp/temp.gpx', outfile)
        md5 = run_command('tail -n1246 %s | md5sum' % outfile, do_popen=True).read().split()[0]
        self.assertEqual(md5, 'e06a6217293b218b8ca1e4dbf07174ce')

        outfile = garmin_base.convert_gmn_to_gpx(txtfile)
        self.assertEqual(None, outfile)

        self.assertFalse(garmin_base.convert_fit_to_tcx(gmnfile))
        self.assertFalse(garmin_base.convert_fit_to_tcx(tcxfile))
        outfile = garmin_base.convert_fit_to_tcx(fitfile)
        self.assertEqual('/tmp/temp.tcx', outfile)
        md5 = run_command('cat %s | md5sum' % outfile, do_popen=True).read().split()[0]
        self.assertEqual(md5, 'e2a7c37233f57c9b7c5da52a01c94210')

        for f in tcxfile, fitfile:
            self.assertEqual(f, garmin_base.convert_gmn_to_xml(f))
        outfile = garmin_base.convert_gmn_to_xml(gmnfile)
        md5 = run_command('cat %s | md5sum' % outfile, do_popen=True).read().split()[0]
        self.assertEqual(md5, 'cdad6ffcd76a7d42ed1947cdfbac3c57')

        gfile = garmin_base.garmin_file(filename=None)
        gfile.filename = gmnfile
        gfile.determine_file_type()
        self.assertFalse(gfile.is_tcx or gfile.is_txt)
        gfile.read_file()
        self.assertEqual(gfile.begin_date, datetime.date(year=2011, month=5, day=7))
        print gfile.begin_time, gfile.begin_date

        gfile = garmin_base.garmin_file(filename=None)
        gfile.filename = tcxfile
        gfile.determine_file_type()
        self.assertFalse(not gfile.is_tcx or gfile.is_txt)
        gfile.read_file()
        self.assertEqual(gfile.begin_date, datetime.date(year=2012, month=11, day=5))

        gfile = garmin_base.garmin_file(filename=None)
        gfile.filename = fitfile
        gfile.determine_file_type()
        self.assertFalse(not gfile.is_tcx or gfile.is_txt)
        gfile.read_file()
        self.assertEqual(gfile.begin_date, datetime.date(year=2014, month=1, day=12))

        gfile = garmin_base.garmin_file(filename=None)
        gfile.filename = txtfile
        gfile.determine_file_type()
        self.assertFalse(gfile.is_tcx or not gfile.is_txt)
        self.assertTrue(gfile.is_txt)
        gfile.read_file_txt()
        gfile.read_file()
        self.assertEqual(gfile.begin_date, datetime.date(year=2013, month=1, day=16))


if __name__ == '__main__':
    unittest.main()
