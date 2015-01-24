#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Unit testing testing...
"""

import unittest
import datetime
import os
import dateutil

import garmin_base
from util import run_command

class TestGarminScript(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        if os.path.exists('temp.csv'):
            os.remove('temp.csv')
        pass

    def test_garmin_base(self):
        gmnfile = 'test/test.gmn'
        tcxfile = 'test/test.tcx'
        fitfile = 'test/test.fit'
        txtfile = 'test/test.txt'

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
        self.assertEqual(md5, '1c304e508709540ccdf44fd70b3c5dcc')

        for f in tcxfile, fitfile:
            self.assertEqual(f, garmin_base.convert_gmn_to_xml(f))
        ### the xml output of garmin_dump uses the local timezone, don't run the test if localtimezone isn't EST
        if datetime.datetime.now(dateutil.tz.tzlocal()).tzname() == 'EST':
            outfile = garmin_base.convert_gmn_to_xml(gmnfile)
            md5 = run_command('cat %s | md5sum' % outfile, do_popen=True).read().split()[0]
            self.assertEqual(md5, 'bce90abae060c7dea4b6b6c3b6466b09')

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

        gfile = garmin_base.garmin_file(gmnfile)
        gdf = garmin_base.garmin_dataframe(garmin_base.garmin_point, gfile.points).dataframe
        gdf.to_csv('temp.csv', index=False)
        md5 = run_command('cat temp.csv | md5sum', do_popen=True).read().split()[0]
        self.assertEqual(md5, 'bd68a0bac5267ccac01139e05883aa8f')
        gdf = garmin_base.garmin_dataframe(garmin_base.garmin_lap, gfile.laps).dataframe
        gdf.to_csv('temp.csv', index=False)
        #print gdf.to_html()
        md5 = run_command('cat temp.csv | md5sum', do_popen=True).read().split()[0]
        self.assertEqual(md5, '10088225057791a97454ca8d5b3cc270')

        gfile = garmin_base.garmin_file(tcxfile)
        gdf = garmin_base.garmin_dataframe(garmin_base.garmin_point, gfile.points).dataframe
        gdf.to_csv('temp.csv', index=False)
        md5 = run_command('cat temp.csv | md5sum', do_popen=True).read().split()[0]
        self.assertEqual(md5, '157e24fa921aaa169dbd6c09cfdd55d5')
        gdf = garmin_base.garmin_dataframe(garmin_base.garmin_lap, gfile.laps).dataframe
        gdf.to_csv('temp.csv', index=False)
        md5 = run_command('cat temp.csv | md5sum', do_popen=True).read().split()[0]
        self.assertEqual(md5, '5973750ba6ffa5394bbc0a4569a2a922')

        gfile = garmin_base.garmin_file(fitfile)
        gdf = garmin_base.garmin_dataframe(garmin_base.garmin_point, gfile.points).dataframe
        gdf.to_csv('temp.csv', index=False)
        md5 = run_command('cat temp.csv | md5sum', do_popen=True).read().split()[0]
        self.assertEqual(md5, '61efed856cab6799bd0bf83a79052c70')
        gdf = garmin_base.garmin_dataframe(garmin_base.garmin_lap, gfile.laps).dataframe
        gdf.to_csv('temp.csv', index=False)
        md5 = run_command('cat temp.csv | md5sum', do_popen=True).read().split()[0]
        self.assertEqual(md5, '13fb54df90be4b3da668da4e2048dcee')

        #opts = {'do_plot': False, 'do_year': False, 'do_month': False, 'do_week': False, 'do_day': False, 'do_file': False, 'do_sport': None, 'do_update': False}
        #garmin_base.do_summary_dataframe('run/2014/12',**opts)

if __name__ == '__main__':
    unittest.main()
