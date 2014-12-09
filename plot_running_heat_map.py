#!/usr/bin/python
# -*- coding: utf-8 -*-

import os , glob
import datetime
from garmin_base import garmin_file, make_mercator_map
from util import run_command
import cPickle

def plot_running_heat_map():
    latlon_lists = []
    gdir = []
    script_path = '/'.join(os.path.abspath(os.sys.argv[0]).split('/')[:-1])
    
    for arg in os.sys.argv[1:]:
        if os.path.isdir(arg):
            gdir.append(arg)
        elif os.path.isdir('%s/run/%s' % (script_path, arg)):
            gdir.append('%s/run/%s' % (script_path, arg))
        elif '-' in arg:
            ent = arg.split('-')
            year = ent[0]
            if len(ent) > 1:
                month = ent[1]
            else:
                month = '*'
            files = glob.glob('%s/run/%s/%s/%s*' % (script_path, year, month, arg)) + glob.glob('%s/run/%s/%s/%s*' % (script_path, year, month, ''.join(ent)))
            basenames = [f.split('/')[-1] for f in sorted(files)]
            if len(filter(lambda x : x[:10] == basenames[0][:10], basenames)) == len(basenames):
                for f in basenames:
                    print f
            gdir += files
        elif '.gmn' in arg or 'T' in arg:
            files = glob.glob('%s/run/*/*/%s' % ( script_path , arg ))
            gdir += files
        else:
            print 'unhandled argument:',arg

    def extract_latlon( fname ):
        lat_vals = []
        lon_vals = []
        gfile = garmin_file(fname)
        print fname
        for point in gfile.points:
            if point.latitude and point.longitude:
                lat_vals.append(point.latitude)
                lon_vals.append(point.longitude)
        latlon_lists.append( [ lat_vals , lon_vals ] )

    def process_files(_, dirname, names):
        for name in names:
            gmn_filename = '%s/%s' % (dirname, name)
            if os.path.isdir(gmn_filename):
                continue
            if '.pkl' in gmn_filename:
                continue
            extract_latlon(gmn_filename)

    if type(gdir) == str:
        if os.path.isdir(gdir):
            os.path.walk(gdir, process_files, None)
        elif os.path.isfile(gdir):
            extract_latlon(gdir)
    if type(gdir) == list:
        for d in gdir:
            if os.path.isdir(d):
                os.path.walk(d, process_files, None)
            elif os.path.isfile(d):
                extract_latlon(d)

    make_mercator_map(name='test_map', title='test_map', latlon_list=latlon_lists)
    return

if __name__ == '__main__':
    plot_running_heat_map()