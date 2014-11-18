#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import datetime
from garmin_base import garmin_file , do_summary , meters_per_mile , sport_types , convert_gmn_to_gpx
from util import run_command

def read_garmin_file( fname ) :
    gfile = garmin_file( fname )

    gfile.print_file_string()
    if gfile.is_txt :
        return
    print ''
    gfile.print_splits( meters_per_mile )
    print ''
    gfile.print_splits( 5000. , 'km' )

    avg_hr = 0
    sum_time = 0
    hr_vals = []
    for point in gfile.points :
        if point.heart_rate > 0 :
            avg_hr += point.heart_rate * point.duration_from_last
            sum_time += point.duration_from_last
            hr_vals.append( point.heart_rate )
    if sum_time > 0 :
        avg_hr /= sum_time
        if len(hr_vals) > 0 :
            print 'Heart Rate %2.2f avg %2.2f max' % ( avg_hr , max(hr_vals) )

    alt_vals = []
    vertical_climb = 0
    for point in gfile.points :
        if point.altitude > 0 :
            alt_vals.append( point.altitude )
            if len(alt_vals) > 1 and alt_vals[-1] > alt_vals[-2] :
                vertical_climb += alt_vals[-1] - alt_vals[-2]
    if len(alt_vals)>0 :
        print 'max altitude diff : %.2f m' % (max(alt_vals) - min(alt_vals) )
        print 'vertical climb : %.2f m' % vertical_climb
    print ''

    gpx_filename = convert_gmn_to_gpx( os.sys.argv[1] )
    if len(os.sys.argv)>2 and os.sys.argv[2] == 'plot' :
        gfile.do_plots()
        gfile.do_map( gpx_filename )
        #os.system( 'rm %s' % gpx_filename )

def compare_with_remote( script_path ) :
    from urllib2 import urlopen
    remote_file_chksum = {}
    remote_file_path = {}
    for line in urlopen( 'https://ddbolineathome.mooo.com/~ddboline/garmin/files/garmin.list' ) :
        md5sum , fname = line.split()[0:2]
        fn = fname.split('/')[-1]
        if fn not in remote_file_chksum :
            remote_file_chksum[fn] = md5sum
            remote_file_path[fn] = '/'.join(fname.split('/')[:-1])
        else :
            print fname , md5sum , remote_file_chksum[fn]

    local_file_chksum = {}
    
    def process_files( arg , dirname , names ) :
        for fn in names :
            fname = '%s/%s' % ( dirname , fn )
            if os.path.isdir( fname ) or fn == 'garmin.pkl' or fn == 'garmin.list' :
                continue
            cmd = 'md5sum %s' % fname
            md5sum = run_command( cmd , do_popen = True ).read().split()[0]
            if fn not in local_file_chksum :
                local_file_chksum[fn] = md5sum
    
    os.path.walk( '%s/run' % script_path , process_files , None )
    
    for fn in remote_file_chksum.keys() :
        if fn not in local_file_chksum.keys() :
            print fn , remote_file_chksum[fn] , remote_file_path[fn]
            run_command( 'wget --no-check-certificate https://ddbolineathome.mooo.com/~ddboline/garmin/files/%s/%s' % ( remote_file_path[fn] , fn ) )
            if os.path.exists( fn ) :
                run_command( 'mv %s %s/run/%s/%s' % ( fn , script_path , remote_file_path[fn] , fn ) )
    return

if __name__ == '__main__' :
    #print os.sys.argv
    script_path = '/'.join( os.path.abspath( os.sys.argv[0] ).split('/')[:-1] )
    
    if '%s/bin' % script_path not in os.getenv( 'PATH' ) :
        os.putenv( 'PATH' , '%s:%s/bin' % ( os.getenv( 'PATH' ) , script_path ) )

    if os.sys.argv[1] == 'get' and not os.path.exists( '%s/run' % script_path ) :
        run_command( 'mkdir -p %s/run/' % script_path )
        os.chdir( '%s/run' % script_path )
        run_command( 'wget --no-check-certificate https://ddbolineathome.mooo.com/~ddboline/backup/garmin_data.tar.gz' )
        run_command( 'tar zxvf garmin_data.tar.gz ; rm garmin_data.tar.gz' )
        exit(0)

    if os.sys.argv[1] == 'sync' :
        compare_with_remote( script_path )
        exit(0)

    if not os.path.exists( '%s/run' % script_path ) :
        print 'need to download files first'
        exit(0)

    options = { 'do_plot' : False , 'do_year' : False , 'do_month' : False , 'do_week' : False , 'do_day' : False , 'do_file' : False , 'do_sport' : None , 'do_update' : False }

    sdir = []
    for arg in os.sys.argv[1:] :
        if arg == 'build' :
            options['build'] = True
        elif arg == 'backup' :
            run_command( 'cd %s/run/ ; tar zcvf %s/garmin_data_%s.tar.gz 2* garmin.pkl' % ( script_path , script_path , datetime.date.today().strftime( '%Y%m%d' ) ) )
        elif arg == 'occur' :
            options['occur'] = True
        elif os.path.isfile( arg ) :
            read_garmin_file( arg )
            exit(0)
        elif arg != 'run' and os.path.isdir( arg ) :
            sdir.append( arg )
        elif arg != 'run' and os.path.isdir( '%s/run/%s' % ( script_path , arg ) ) :
            sdir.append( '%s/run/%s' % ( script_path , arg ) )
        elif arg in options :
            options[arg] = True
        elif 'do_%s' % arg in options :
            options['do_%s' % arg] = True
        else :
            spts = filter( lambda x : arg in x , sport_types )
            if len(spts) > 0 :
                options['do_sport'] = spts[0]
    if not sdir :
        sdir.append( '%s/run' % script_path )
    do_summary( sdir , **options )
