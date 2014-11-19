#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import xml.dom.minidom
import tempfile
import datetime
import cPickle
import lockfile
from util import run_command

from garmin_list_of_corrected_laps import list_of_corrected_laps, \
    is_biking_file , is_running_file , is_walking_file , is_stair_file , \
    list_of_skiing_files , list_of_snowshoeing_files , list_of_running_files_by_time , list_of_walking_files_by_time , list_of_biking_files_by_time

hostname = os.uname()[1]

### Useful constants
meters_per_mile = 1609.344 # meters
marathon_distance_m = 42195 # meters
marathon_distance_mi = marathon_distance_m / meters_per_mile # meters

### explicitly specify available types...
sport_types = ( 'running' , 'biking' , 'walking' , 'ultimate' , 'elliptical' , 'stairs' , 'lifting' , 'swimming' , 'other' , 'snowshoeing' , 'skiing' )

month_names = ( 'Jan' , 'Feb' , 'Mar' , 'Apr' , 'May' , 'Jun' , 'Jul' , 'Aug' , 'Sep' , 'Oct' , 'Nov' , 'Dec' )

weekday_names = ( 'Mon' , 'Tue' , 'Wed' , 'Thu' , 'Fri' , 'Sat' , 'Sun' )

if hostname == 'dilepton-tower' or hostname == 'dilepton2' :
    mainlock = '/home/ddboline/Dropbox/backup/.garmin.lock.new'
else :
    mainlock = '/tmp/.garmin.lock.new'

global_lockfiles = {}

def get_lockfile( lf = mainlock ) :
    ''' function to obtain lockfile '''
    if hostname != 'dilepton-tower' and hostname != 'dilepton2' :
        return
    global_lockfiles[lf] = lockfile.FileLock( lf )
    try :
        global_lockfiles[lf].acquire(timeout=60)
    except lockfile.LockTimeout :
        global_lockfiles[lf].break_lock()
        global_lockfiles[lf].acquire()

def remove_lockfile( lf = mainlock ) :
    ''' function to unlock, remove lockfile '''
    if hostname != 'dilepton-tower' and hostname != 'dilepton2' :
        return
    if lf in global_lockfiles :
        global_lockfiles[lf].release()
    else :
        os.remove( lf )

def days_in_year( year = datetime.date.today().year ) :
    ''' return number of days in a given year '''
    return (datetime.date( year=year+1 , month=1 , day=1 )-datetime.date( year=year , month=1 , day=1 )).days

def days_in_month( month = datetime.date.today().month , year = datetime.date.today().year ) :
    ''' return number of days in a given month '''
    y1 = year
    m1 = month + 1
    if m1 == 13 :
        m1 = 1
        y1 += 1
    return (datetime.date( year=y1 , month=m1 , day=1 )-datetime.date( year=year , month=month , day=1 )).days

### maybe change output to datetime object?
def convert_date_string( date_str ) :
    ''' convert date string to datetime object '''
    import dateutil.parser
    return dateutil.parser.parse( date_str , ignoretz = True )

def expected_calories( weight = 175 , pace_min_per_mile = 10.0 , distance = 1.0 ) :
    ''' return expected calories for running at a given pace '''
    cal_per_mi = weight * ( 0.0395 + 0.00327 * (60./pace_min_per_mile) + 0.000455 * (60./pace_min_per_mile)**2 + 0.000801 * (weight/154) * 0.425 / weight * (60./pace_min_per_mile)**3 ) * 60. / (60./pace_min_per_mile)
    return cal_per_mi * distance

def print_date_string( d ) :
    ''' datetime object to standardized string '''
    return d.strftime( '%Y-%m-%dT%H:%M:%SZ' )

def convert_time_string( time_str ) :
    ''' time string to seconds '''
    hour = int(time_str.split(':')[0])
    minute = int(time_str.split(':')[1])
    second = float(time_str.split(':')[2])
    return second + 60*( minute + 60 * ( hour ) )

def print_h_m_s( second , do_hours = True ) :
    ''' seconds to hh:mm:ss string '''
    hours = int( second / 3600 )
    minutes = int( second / 60 ) - hours * 60
    seconds = int( second ) - minutes * 60 - hours * 3600
    if hours > 0 :
        return '%02i:%02i:%02i' % ( hours , minutes , seconds )
    elif hours == 0 :
        if do_hours :
            return '00:%02i:%02i' % ( minutes , seconds )
        else :
            return '%02i:%02i' % ( minutes , seconds )

def getText(nodelist):
    ''' global function for reading xml file '''
    rc = []
    for node in nodelist.childNodes:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def convert_gmn_to_gpx( gmn_filename ) :
    ''' create temporary gpx file from gmn or tcx files '''
    if gmn_filename.find( '.fit' ) >= 0 or gmn_filename.find( '.FIT' ) >= 0 :
        tcx_filename = convert_fit_to_tcx( gmn_filename )
        run_command( 'gpsbabel -i gtrnctr -f %s -o gpx -F /tmp/temp.gpx ' % ( tcx_filename ) )
    elif gmn_filename.find( '.tcx' ) >= 0 or gmn_filename.find( '.TCX' ) >= 0 :
        run_command( 'gpsbabel -i gtrnctr -f %s -o gpx -F /tmp/temp.gpx' % gmn_filename )
    else :
        run_command( 'garmin_gpx %s > /tmp/temp.gpx' % gmn_filename )
    return '/tmp/temp.gpx'

def convert_fit_to_tcx( fit_filename ) :
    ''' fit files to tcx files '''
    if fit_filename.find( '.fit' ) >= 0 or fit_filename.find( '.FIT' ) >= 0 :
        run_command( 'fit2tcx %s > /tmp/temp.tcx' % fit_filename )
    else :
        return False
    return '/tmp/temp.tcx'

def convert_gmn_to_xml( gmn_filename ) :
    ''' create temporary xml file from gmn, much of the complexity is to deal with hacks. '''
    if any( [ a in gmn_filename for a in ( '.tcx' , '.TCX' , '.fit' , '.FIT' , '.xml' , '.txt' ) ] ) :
        return gmn_filename
    xml_file = tempfile.NamedTemporaryFile(delete=False)
    xml_filename = xml_file.name
    xml_file.write( '<root>\n' )
    
    is_bike , is_run , is_walk , is_stair = is_biking_file( gmn_filename ) , is_running_file( gmn_filename ) , is_walking_file( gmn_filename ) , is_stair_file( gmn_filename )
    
    for l in run_command( 'garmin_dump %s' % gmn_filename , do_popen = True ) :
        ### Now the hack, read each line, modify selected lines if desired
        line = l.strip()
        if is_bike :
            if 'sport' in line :
                line = line.replace( 'running' , 'biking' )
            if 'calories' in line :
                newcal = float(line.split('>')[1].split('<')[0]) * ( 1701/26.26 ) / ( 3390/26.43 )
                line = '<calories>%i</calories>' % int(newcal)
        if is_run :
            if 'sport' in line :
                line = line.replace( 'biking' , 'running' )
            if 'calories' in line :
                newcal = float(line.split('>')[1].split('<')[0]) * ( 3390/26.43 ) / ( 1701/26.26 )
                line = '<calories>%i</calories>' % int(newcal)
        if is_walk :
            if 'sport' in line :
                line = line.replace( 'running' , 'walking' )
        if is_stair :
            if line.find( 'sport' ) >= 0 :
                line = line.replace( 'running' , 'stairs' )
        xml_file.write( line + '\n' )
    xml_file.write( '</root>\n' )
    xml_file.close()
    os.system( 'cp %s /tmp/temp.xml' % xml_file.name )
    return xml_filename

class garmin_point(object) :
    '''
        point representing each gps point
            functions:
                read_point_xml( node ) , read_point_tcx( node )
    '''
    def __init__( self , time = None , latitude = None , longitude = None , altitude = 0 , distance = 0 , heart_rate = 0 ) :
        self.time = time
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.distance = distance
        self.heart_rate = heart_rate
        ### These are set by garmin_file class, left here as placeholders
        self.duration_from_last = 0 ### here last will mean last track point, resets at every new track
        self.duration_from_begin = 0 ### here we add up durations, ignoring time between tracks
        self.speed_permi = 0
        self.speed_mph = 0
        self.avg_speed_value_permi = 0
        self.avg_speed_value_mph = 0

    def read_point_xml( self , node ) :
        ''' read point from xml file (generated from binary gmn file '''
        self.time = convert_date_string( node.getAttribute('time') )
        lat = node.getAttribute('lat')
        if lat != '' :
            self.latitude = float( lat )
        lon = node.getAttribute('lon')
        if lon != '' :
            self.longitude = float( lon )
        alt = node.getAttribute('alt')
        if alt != '' :
            self.altitude = float( alt )
        dist = node.getAttribute('distance')
        if dist != '' :
            self.distance = float( dist )
        hr = node.getAttribute('hr')
        if hr != '' :
            self.heart_rate = int( hr )
        return None

    def read_point_tcx( self , node ) :
        ''' read point from tcx file (generated by gant, converted from fit files) '''
        self.time = convert_date_string( getText(node.getElementsByTagName('Time')[0]) )
        lat = ''
        lon = ''
        for L in node.getElementsByTagName( 'Position' ) :
            lat = getText(L.getElementsByTagName('LatitudeDegrees')[0])
            lon = getText(L.getElementsByTagName('LongitudeDegrees')[0])
        if lat != '' :
            self.latitude = float( lat )
        if lon != '' :
            self.longitude = float( lon )
        tmp = node.getElementsByTagName('AltitudeMeters')
        if len(tmp) > 0 :
            alt = getText(node.getElementsByTagName('AltitudeMeters')[0])
            if alt != '' :
                self.altitude = float( alt )
        tmp = node.getElementsByTagName('DistanceMeters')
        if len(tmp) > 0 :
            dist = getText(node.getElementsByTagName('DistanceMeters')[0])
            if dist != '' :
                self.distance = float( dist )
        hr = ''
        for L in node.getElementsByTagName( 'HeartRateBpm' ) :
            hr = getText(L.getElementsByTagName('Value')[0])
        if hr != '' :
            self.heart_rate = int( hr )
        return None

class garmin_lap(object) :
    '''
        class representing each lap in xml file
            functions:
                read_lap_xml( node ) , read_lap_tcx( node ) , print_lap_string( node )
    '''
    def __init__( self , lap_type = None , lap_index = 0 , lap_start = None , lap_duration = 0.0 , lap_distance = 0.0 , lap_trigger = None , lap_max_speed = None , lap_calories = 0 , lap_avg_hr = -1 , lap_max_hr = -1 , lap_intensity = None , lap_number = 0 ) :
        self.lap_type = lap_type
        self.lap_index = lap_index
        self.lap_start = lap_start
        self.lap_duration = lap_duration
        self.lap_distance = lap_distance
        self.lap_trigger = lap_trigger
        self.lap_max_speed = lap_max_speed
        self.lap_calories = lap_calories
        self.lap_avg_hr = lap_avg_hr
        self.lap_max_hr = lap_max_hr
        self.lap_intensity = lap_intensity
        self.lap_number = lap_number
        self.lap_start_string = ''

    def read_lap_xml( self, node ) :
        ''' read lap from xml file '''
        self.lap_type = node.getAttribute('type')
        self.lap_index = int(node.getAttribute('index'))
        self.lap_start_string = node.getAttribute('start')
        self.lap_start = convert_date_string( self.lap_start_string )
        self.lap_duration = float( convert_time_string( node.getAttribute('duration') ) )
        self.lap_distance = float( node.getAttribute('distance') )
        self.lap_trigger = node.getAttribute('trigger')
        self.lap_max_speed = float(getText(node.getElementsByTagName('max_speed')[0]))
        self.lap_calories = int(getText(node.getElementsByTagName('calories')[0]))
        tmp = node.getElementsByTagName('avg_hr')
        if len(tmp) > 0 :
            self.lap_avg_hr = int(getText(node.getElementsByTagName('avg_hr')[0]))
        tmp = node.getElementsByTagName('max_hr')
        if len(tmp) > 0 :
            self.lap_max_hr = int(getText(node.getElementsByTagName('max_hr')[0]))
        self.lap_intensity = getText(node.getElementsByTagName('intensity')[0])
        return None

    def read_lap_tcx( self , node ) :
        ''' read lap from tcx file '''
        self.lap_start_string = node.getAttribute('StartTime')
        self.lap_start = convert_date_string( self.lap_start_string )
        self.lap_duration = float( getText(node.getElementsByTagName('TotalTimeSeconds')[0]) )
        self.lap_distance = float( getText(node.getElementsByTagName('DistanceMeters')[0] ) )
        self.lap_trigger = node.getAttribute('TriggerMethod')
        try :
            self.lap_max_speed = float(getText(node.getElementsByTagName('MaximumSpeed')[0]))
        except IndexError :
            return None
        self.lap_calories = int(getText(node.getElementsByTagName('Calories')[0]))
        tmp = node.getElementsByTagName('AverageHeartRateBpm')
        if len(tmp) > 0 :
            self.lap_avg_hr = int(getText(node.getElementsByTagName('Value')[0]))
        tmp = node.getElementsByTagName('MaximumHeartRateBpm')
        if len(tmp) > 0 :
            self.lap_max_hr = int(getText(node.getElementsByTagName('Value')[0]))
        self.lap_intensity = getText(node.getElementsByTagName('Intensity')[0])
        return None

    def print_lap_string( self , sport ) :
        ''' print nice output for a lap '''
        print '%s lap %i %.2f mi %s %s calories %.2f min' % ( sport , self.lap_number , self.lap_distance / meters_per_mile , print_h_m_s( self.lap_duration ) , self.lap_calories , self.lap_duration / 60. ) ,
        if sport == 'running' :
            if self.lap_distance > 0 :
                print print_h_m_s( self.lap_duration / ( self.lap_distance / meters_per_mile ) , False ) , '/ mi ',
                print print_h_m_s( self.lap_duration / ( self.lap_distance / 1000. ) , False ) , '/ km',
        if self.lap_avg_hr > 0 :
            print '%i bpm' % self.lap_avg_hr
        else :
            print ''

        return None

class garmin_file(object) :
    '''
        class representing a full xml file
            functions:
                read_file() , read_file_tcx() , read_file_xml() , print_file_string() , calculate_speed() , print_splits() , do_map( gpx_filename ) , do_plots()
    '''
    def __init__( self , filename = '' , is_tcx = False , is_txt = False ) :
        self.filename = filename
        self.track_points = []
        self.begin_time = None
        self.begin_date = None
        self.sport = None
        self.total_calories = 0
        self.total_distance = 0
        self.total_duration = 0
        self.total_hr_dur = 0
        self.laps = []
        self.points = []
        self.is_tcx = is_tcx
        self.is_txt = is_txt
        self.graphs = []
        
        if self.filename :
            self.determine_file_type()
            self.filename = convert_gmn_to_xml( self.filename )
            self.read_file()

    def __del__( self ) :
        if self.filename and not self.is_tcx and not self.is_txt :
            run_command( 'rm %s' % self.filename )
            pass

    def determine_file_type( self ) :
        if '.tcx' in self.filename or '.TCX' in self.filename :
            self.is_tcx = True
        if '.txt' in self.filename or '.TXT' in self.filename :
            self.is_txt = True
        if '.fit' in self.filename or '.FIT' in self.filename :
            self.filename = convert_fit_to_tcx( self.filename )
            self.is_tcx = True

    def is_running( self ) :
        ''' is running? or other sport? '''
        if self.sport == 'running' :
            return True
        else :
            return False

    def read_file( self ) :
        ''' read file, use is_tcx/is_txt to decide which function to call '''
        if self.is_tcx :
            self.read_file_tcx()
        elif self.is_txt :
            self.read_file_txt()
        else :
            self.read_file_xml()
        self.begin_time = self.laps[0].lap_start
        self.begin_date = self.begin_time.date()
        if print_date_string( self.begin_time ) in list_of_skiing_files :
            self.sport = 'skiing'
        if print_date_string( self.begin_time ) in list_of_snowshoeing_files :
            self.sport = 'snowshoeing'
        if print_date_string( self.begin_time ) in list_of_running_files_by_time :
            self.sport = 'running'
        if print_date_string( self.begin_time ) in list_of_walking_files_by_time :
            self.sport = 'walking'
        if print_date_string( self.begin_time ) in list_of_biking_files_by_time :
            self.sport = 'biking'
        self.calculate_speed()

    def read_file_txt( self ) :
        ''' read txt file, these just contain summary information '''
        for line in open( self.filename , 'r' ).readlines() :
            cur_lap = garmin_lap()
            cur_point = garmin_point()

            for ent in line.split() :
                if ent.find( '=' ) < 0 :
                    continue
                key = ent.split('=')[0]
                val = ent.split('=')[1]
                if key == 'date' :
                    year = int(val[0:4])
                    month = int(val[4:6])
                    day = int(val[6:8])
                    cur_lap.lap_start = datetime.datetime( year , month , day )
                    cur_point.time = datetime.datetime( year , month , day )
                    if len(self.points) == 0 :
                        self.points.append( cur_point )
                        cur_point = garmin_point( time = cur_point.time )
                if key == 'time' :
                    hour = int(val[0:2])
                    minute = int(val[2:4])
                    second = int(val[4:6])
                    cur_lap.lap_start.hour = hour
                    cur_lap.lap_start.minute = minute
                    cur_lap.lap_start.second = second
                if key == 'type' :
                    self.sport = val
                if key == 'lap' :
                    cur_lap.lap_number = int( val )
                if key == 'dur' :
                    cur_lap.lap_duration = float( convert_time_string( val ) )
                    cur_point.time = self.points[-1].time + datetime.timedelta( seconds = cur_lap.lap_duration )
                if key == 'dis' :
                    if val.find( 'mi' ) >= 0 : # specify mi, m or assume it's meters
                        cur_lap.lap_distance = float( val.split('mi')[0] ) * meters_per_mile
                    elif val.find( 'm' ) >= 0 :
                        cur_lap.lap_distance = float( val.split('m')[0] )
                    else :
                        cur_lap.lap_distance = float( val )
                    cur_point.distance = self.points[-1].distance + cur_lap.lap_distance
                if key == 'cal' :
                    cur_lap.lap_calories = int( val )
                if key == 'avghr' :
                    cur_lap.lap_avg_hr = float( val )
                    cur_point.heart_rate = cur_lap.lap_avg_hr
            if cur_lap.lap_calories == -1 :
                dur = cur_lap.lap_duration / 60.
                dis = cur_lap.lap_distance / meters_per_mile
                pace = dur / dis
                cur_lap.lap_calories = int( expected_calories( weight = 175 , pace_min_per_mile = pace , distance = dis ) )
            self.total_calories += cur_lap.lap_calories
            self.total_distance += cur_lap.lap_distance
            self.total_duration += cur_lap.lap_duration
            if cur_lap.lap_avg_hr :
                self.total_hr_dur += cur_lap.lap_avg_hr * cur_lap.lap_duration
            self.laps.append( cur_lap )
            self.points.append( cur_point )

        time_since_begin = 0
        for idx in range(1,len(self.points)) :
            if self.points[idx].distance > self.points[idx-1].distance :
                self.points[idx].duration_from_last = ( self.points[idx].time - self.points[idx-1].time ).total_seconds()
                time_since_begin += self.points[idx].duration_from_last
                self.points[idx].duration_from_begin = time_since_begin
            else :
                self.points[idx].duration_from_last = 0

        return None

    def read_file_tcx( self ) :
        ''' read tcx file '''
        is_bad_run = False
        is_bad_bike = False
        doc = xml.dom.minidom.parse(self.filename)
        for node in doc.getElementsByTagName('Activities') :
            for node2 in node.getElementsByTagName( 'Activity' ) :
                self.sport = node2.getAttribute( 'Sport' ).lower()
                if is_biking_file( self.filename ) :
                    self.sport = 'biking'
                    is_bad_run = True
                if is_running_file( self.filename ) :
                    self.sport = 'running'
                    is_bad_bike = True
                lap_number = 0
                corrected_laps = {}
                time_from_begin = 0
                for node3 in node2.getElementsByTagName( 'Lap' ) :
                    cur_lap = garmin_lap()
                    cur_lap.read_lap_tcx( node3 )
                    if len(self.laps) == 0 and print_date_string( cur_lap.lap_start ) in list_of_corrected_laps :
                        corrected_laps = list_of_corrected_laps[print_date_string( cur_lap.lap_start )]
                    for node4 in node3.getElementsByTagName( 'Track' ) : ### every time you stop then start watch a new track is created...
                        is_beginning_of_track = True
                        for node5 in node4.getElementsByTagName( 'Trackpoint' ) :
                            cur_point = garmin_point()
                            cur_point.read_point_tcx( node5 )
                            if len(self.points) == 0 :
                                cur_point.duration_from_last = 0
                                is_beginning_of_track = False
                            else :
                                if is_beginning_of_track :
                                    cur_point.duration_from_last = 0
                                    is_beginning_of_track = False
                                else :
                                    cur_point.duration_from_last = ( cur_point.time - self.points[-1].time ).total_seconds()
                            time_from_begin += cur_point.duration_from_last
                            cur_point.duration_from_begin = time_from_begin
                            self.points.append( cur_point )
                    if lap_number in corrected_laps :
                        if type(corrected_laps[lap_number]) == float or type(corrected_laps[lap_number]) == int :
                            cur_lap.lap_distance = corrected_laps[lap_number] * meters_per_mile
                        elif len(corrected_laps[lap_number]) == 1 :
                            cur_lap.lap_distance = corrected_laps[lap_number] * meters_per_mile
                        else :
                            cur_lap.lap_distance = corrected_laps[lap_number][0] * meters_per_mile
                            cur_lap.lap_duration = corrected_laps[lap_number][1]
                    cur_lap.lap_number = lap_number
                    if is_bad_run :
                        cur_lap.lap_calories = int( cur_lap.lap_calories * ( 1701/26.26 ) / ( 3390/26.43 ) )
                    if is_bad_bike :
                        cur_lap.lap_calories = int( cur_lap.lap_calories * ( 3390/26.43 ) / ( 1701/26.26 ) )
                    lap_number += 1
                    self.laps.append( cur_lap )
                    self.total_distance += cur_lap.lap_distance
                    self.total_calories += cur_lap.lap_calories
                    self.total_duration += cur_lap.lap_duration
                    if cur_lap.lap_avg_hr :
                        self.total_hr_dur += cur_lap.lap_avg_hr * cur_lap.lap_duration

        return None

    def read_file_xml( self ) :
        ''' read xml file '''
        doc = xml.dom.minidom.parse(self.filename)

        for node in doc.getElementsByTagName('run'):
            run_type = node.getAttribute('type')
            track = node.getAttribute('track')
            self.sport = node.getAttribute('sport')
            multisport = node.getAttribute('multisport')

            L = node.getElementsByTagName( 'laps' )
            for node2 in L :
                begin_lap = node2.getAttribute('first')
                end_lap = node2.getAttribute('last')

        lap_number = 0
        corrected_laps = {}
        for node in doc.getElementsByTagName('lap') :
            cur_lap = garmin_lap()
            cur_lap.read_lap_xml( node )
            cur_lap.lap_number = lap_number
            if len(self.laps) ==  0 and print_date_string( cur_lap.lap_start ) in list_of_corrected_laps :
                corrected_laps = list_of_corrected_laps[print_date_string( cur_lap.lap_start )]
            if lap_number in corrected_laps :
                if type(corrected_laps[lap_number]) == float or len(corrected_laps[lap_number]) == 1 :
                    cur_lap.lap_distance = corrected_laps[lap_number] * meters_per_mile
                else :
                    cur_lap.lap_distance = corrected_laps[lap_number][0] * meters_per_mile
                    cur_lap.lap_duration = corrected_laps[lap_number][1]
            lap_number += 1
            self.laps.append( cur_lap )
            self.total_distance += cur_lap.lap_distance
            self.total_calories += cur_lap.lap_calories
            self.total_duration += cur_lap.lap_duration
            if cur_lap.lap_avg_hr :
                self.total_hr_dur += cur_lap.lap_avg_hr * cur_lap.lap_duration

        time_from_begin = 0

        for node in doc.getElementsByTagName('point'):
            cur_point = garmin_point()
            cur_point.read_point_xml( node )

            if len(self.points) == 0 :
                cur_point.duration_from_last = 0
            else :
                cur_point.duration_from_last = ( cur_point.time - self.points[-1].time ).total_seconds()
            time_from_begin += cur_point.duration_from_last
            cur_point.duration_from_begin = time_from_begin

            if cur_point.distance > 0 :
                self.points.append( cur_point )

        return None

    def print_file_string( self ):
        ''' nice output string for a file '''
        print 'Start time' , print_date_string( self.begin_time )
        for lap in self.laps :
            lap.print_lap_string( self.sport )

        min_mile = 0
        mi_per_hr = 0
        if self.total_distance > 0 :
            min_mile = ( self.total_duration / 60. ) / ( self.total_distance / meters_per_mile )
        if self.total_duration > 0 :
            mi_per_hr = ( self.total_distance / meters_per_mile ) / ( self.total_duration/60./60. )

        if self.is_running() :
            print 'total %.2f mi %s calories %s time %s min/mi %s min/km' % ( self.total_distance / meters_per_mile , self.total_calories , print_h_m_s( self.total_duration ) , print_h_m_s( min_mile*60 , False ) , print_h_m_s( min_mile*60 / meters_per_mile * 1000. , False ) ),
        else :
            print 'total %.2f mi %s calories %s time %.2f mph' % ( self.total_distance / meters_per_mile , self.total_calories , print_h_m_s( self.total_duration ) , mi_per_hr ),
        if self.total_hr_dur > 0 :
            print '%i bpm' % ( self.total_hr_dur / self.total_duration )
        else :
            print ''

        return None

    def calculate_speed( self ) :
        ''' calculate instantaneous speed (could maybe be a bit more elaborate?) '''
        N = 5
        if len(self.points) < N : return None
        for idx in range( 1 , len(self.points) ) :
            jdx = idx - N
            if jdx < 0 : jdx = idx - 1
            totdur = ( self.points[idx].time - self.points[jdx].time ).total_seconds() # seconds
            totdis = self.points[idx].distance - self.points[jdx].distance # meters
            if totdis > 0 :
                self.points[idx].speed_permi = (totdur/60.) / (totdis/meters_per_mile)
            if totdur > 0 :
                self.points[idx].speed_mph = (totdis/meters_per_mile) / (totdur/60./60.)
            if self.points[idx].distance > 0 :
                self.points[idx].avg_speed_value_permi = ( ( self.points[idx].time - self.points[0].time ).total_seconds()/60. ) / ( self.points[idx].distance/meters_per_mile )
            if ( self.points[idx].time - self.points[0].time ).total_seconds() > 0 :
                self.points[idx].avg_speed_value_mph = ( self.points[idx].distance/meters_per_mile ) / ( ( self.points[idx].time - self.points[0].time ).total_seconds()/60./60. )
        return None

    def print_splits( self , split_distance_in_meters , label = 'mi' ) :
        ''' print split time for given split distance '''
        if len(self.points) == 0 : return None
        last_point_me = 0
        last_point_time = 0
        prev_split_me = 0
        prev_split_time = 0
        avg_hrt_rate = 0

        for point in self.points :
            cur_point_me = point.distance
            cur_point_time = point.duration_from_begin
            if ( cur_point_me - last_point_me ) <= 0 :
                continue
            avg_hrt_rate += point.heart_rate * ( cur_point_time - last_point_time )
            nmiles = int(cur_point_me/split_distance_in_meters) - int(last_point_me/split_distance_in_meters)
            if nmiles > 0 :
                cur_split_me = int(cur_point_me/split_distance_in_meters)*split_distance_in_meters
                cur_split_time = last_point_time + ( cur_point_time - last_point_time ) / ( cur_point_me - last_point_me ) * ( cur_split_me - last_point_me )
                time_val = ( cur_split_time - prev_split_time )
                split_dist = cur_point_me/split_distance_in_meters
                if label == 'km' :
                    split_dist = cur_point_me/1000.

                if nmiles > 1 :
                    for nmi in range( 0 , nmiles ) :
                        if self.is_running() :
                            print '%i %s \t' % ( split_dist / nmiles + nmi , label ) , print_h_m_s( time_val  / nmiles ) , '\t' , print_h_m_s( time_val / nmiles / ( split_distance_in_meters / meters_per_mile ) , False ) , '/ mi\t' , print_h_m_s( time_val / nmiles / ( split_distance_in_meters / 1000. ) , False ) , '/ km\t' , print_h_m_s( time_val / nmiles / ( split_distance_in_meters / meters_per_mile ) * marathon_distance_mi ) ,
                            if avg_hrt_rate > 0 :
                                print '\t %i bpm avg' % ( avg_hrt_rate / ( cur_split_time - prev_split_time ) )
                            else :
                                print ''
                        else :
                            print '%i %s \t' % ( split_dist / nmiles + nmi , label ) , print_h_m_s( time_val / nmiles ) , '\t' , '%.2f mph' % ( 1. / ( time_val / nmiles / ( split_distance_in_meters / meters_per_mile ) / 60. / 60. ) ) ,
                            if avg_hrt_rate > 0 :
                                print '\t %i bpm avg' % ( avg_hrt_rate / ( cur_split_time - prev_split_time ) )
                            else :
                                print ''
                else :
                    if self.is_running() :
                        print '%i %s \t' % ( split_dist , label ) , print_h_m_s( time_val ) , '\t' , print_h_m_s( time_val / ( split_distance_in_meters / meters_per_mile ) , False ) , '/ mi\t' , print_h_m_s( time_val / ( split_distance_in_meters / 1000. ) , False ) , '/ km\t' , print_h_m_s( time_val / ( split_distance_in_meters / meters_per_mile ) * marathon_distance_mi ) ,
                        if avg_hrt_rate > 0 :
                            print '\t %i bpm avg' % ( avg_hrt_rate / ( cur_split_time - prev_split_time ) )
                        else :
                            print ''
                    else :
                        print '%i %s \t' % ( split_dist , label ) , print_h_m_s( time_val ) , '\t' , '%.2f mph' % ( 1. / ( time_val / ( split_distance_in_meters / meters_per_mile ) / 60. / 60. ) ) ,
                        if avg_hrt_rate > 0 :
                            print '\t %i bpm avg' % ( avg_hrt_rate / ( cur_split_time - prev_split_time ) )
                        else :
                            print ''

                prev_split_me = cur_split_me
                prev_split_time = cur_split_time
                avg_hrt_rate = 0
            last_point_me = cur_point_me
            last_point_time = cur_point_time

        return None

    def do_map( self , gpx_filename ) :
        ''' wrapper around gpxviewer '''
        if gpx_filename :
            run_command( 'gpxviewer %s' % gpx_filename )

    def do_plots( self , use_time = False ) :
        ''' create pretty plots using ROOT '''
        avg_hr = 0
        sum_time = 0
        max_hr = 0
        hr_vals = []
        hr_values = []
        alt_vals = []
        alt_values = []
        vertical_climb = 0
        speed_values = []
        mph_speed_values = []
        avg_speed_values = []
        avg_mph_speed_values = []
        lat_vals = []
        lon_vals = []
        for point in self.points :
            if use_time :
                xval = point.duration_from_begin
            else :
                xval = point.distance / meters_per_mile
            if point.heart_rate > 0 :
                avg_hr += point.heart_rate * point.duration_from_last
                sum_time += point.duration_from_last
                hr_vals.append( point.heart_rate )
                hr_values.append( [ xval , point.heart_rate ] )
            if point.altitude > 0 :
                alt_vals.append( point.altitude )
                if len(alt_vals) > 1 and alt_vals[-1] > alt_vals[-2] :
                    vertical_climb += alt_vals[-1] - alt_vals[-2]
                alt_values.append( [ xval , point.altitude ] )
            if point.speed_permi > 0 and point.speed_permi < 20 :
                speed_values.append( [ xval , point.speed_permi ] )
            if point.speed_mph > 0 and point.speed_mph < 20 :
                mph_speed_values.append( [ xval , point.speed_mph ] )
            if point.avg_speed_value_permi > 0 and point.avg_speed_value_permi < 20 :
                avg_speed_values.append( [ xval , point.avg_speed_value_permi ] )
            if point.avg_speed_value_mph > 0 :
                avg_mph_speed_values.append( [ xval , point.avg_speed_value_mph ] )
            if point.latitude and point.longitude :
                lat_vals.append( point.latitude )
                lon_vals.append( point.longitude )
        if sum_time > 0 :
            avg_hr /= sum_time
            max_hr = max(hr_vals)

        if len(hr_vals) > 0 :
            print 'Heart Rate %2.2f avg %2.2f max' % ( avg_hr , max(hr_vals) )

        if len(alt_vals)>0 :
            print 'max altitude diff : %.2f m' % (max(alt_vals) - min(alt_vals) )
            print 'vertical climb : %.2f m' % vertical_climb

        def plot_graph_root( name = None , title = None , data = None , **opts ) :
            ''' convenience function '''
            import numpy as np
            from ROOT import TCanvas , TGraph
            x , y = zip( *data )
            xa = np.array( x )
            ya = np.array( y )
            canv = TCanvas(title,title)
            graph = TGraph(len(x),xa,ya)
            if title :
                graph.SetTitle( title )
            if data :
                graph.Draw('A*')
            canv.Update()
            return [ canv , graph ]

        def plot_graph_pyplot( name = None , title = None , data = None , **opts ) :
            import numpy as np
            import matplotlib
            matplotlib.use( 'Agg' )
            import matplotlib.pyplot as plt
            plt.clf()
            x , y = zip( *data )
            xa = np.array( x )
            ya = np.array( y )
            plt.plot( xa , ya )
            plt.title( title )
            plt.savefig('%s.png' % name)
            return '%s.png' % name

        def plot_graph( name = None , title = None , data = None , **opts ) :
            #return plot_graph_root( name , title , data )
            return plot_graph_pyplot( name , title , data )
        
        def make_mercator_map( name = None , title = None , lats = None , lons = None , **opts ) :
            import matplotlib
            matplotlib.use( 'Agg' )
            from mpl_toolkits.basemap import Basemap
            import numpy as np
            import matplotlib.pyplot as plt
            plt.clf()
            x = np.array( lons )
            y = np.array( lats )

            latcent = ( y.max() + y.min() ) / 2.
            loncent = ( x.max() + x.min() ) / 2.
            latwidth = abs(y.max() - y.min())
            lonwidth = abs(x.max() - x.min())
            width = max( latwidth , lonwidth )
            latmin = latcent - 0.6 * width
            latmax = latcent + 0.6 * width
            lonmin = loncent - 0.6 * width
            lonmax = loncent + 0.6 * width
            
            m = Basemap(projection='merc' , llcrnrlat=latmin , urcrnrlat=latmax , llcrnrlon=lonmin , urcrnrlon=lonmax , resolution='h' )
            m.drawcoastlines()
            m.fillcontinents(color='coral',lake_color='aqua')
            m.drawstates()
            m.drawcounties()
            
            m.plot( x , y , latlon = True )
            
            plt.title( title )
            plt.xlabel( 'longitude deg' )
            plt.ylabel( 'latitude deg' )
            plt.savefig( '%s.png' % name )
        
        curpath = os.path.realpath( os.path.curdir )
        print curpath
        if not os.path.exists( '%s/html' % curpath ) :
            os.makedirs( '%s/html' % curpath )
        os.chdir( '%s/html' % curpath )
        
        if len(hr_values) > 0 :
            self.graphs.append( plot_graph( name = 'heart_rate' , title = 'Heart Rate %2.2f avg %2.2f max' % ( avg_hr , max_hr ) , data = hr_values ) )
        if len(alt_values) > 0 :
            self.graphs.append( plot_graph( name = 'altitude' , title = 'Altitude' , data = alt_values ) )
        if len(speed_values) > 0 :
            self.graphs.append( plot_graph( name = 'speed_minpermi' , title = 'Speed min/mi' , data = speed_values ) )
            self.graphs.append( plot_graph( name = 'speed_mph' , title = 'Speed mph' , data = mph_speed_values ) )

        if len(avg_speed_values) > 0 :
            avg_speed_value_min = int(avg_speed_values[-1][1])
            avg_speed_value_sec = int( ( avg_speed_values[-1][1] - avg_speed_value_min ) * 60. )
            self.graphs.append( plot_graph( name = 'avg_speed_minpermi' , title = 'Avg Speed %i:%02i min/mi' % ( avg_speed_value_min , avg_speed_value_sec ) , data = avg_speed_values ) )

        if len(avg_mph_speed_values) > 0 :
            avg_mph_speed_value = avg_mph_speed_values[-1][1]
            self.graphs.append( plot_graph( name = ' avg_speed_mph' , title = 'Avg Speed %.2f mph' % avg_mph_speed_value , data = avg_mph_speed_values ) )
        
        make_mercator_map( name = 'route_map' , title = 'Route Map' , lats = lat_vals , lons = lon_vals )
        
        os.chdir( curpath )

def compute_file_md5sum( filename ) :
    ''' wrapper around md5sum '''
    gmn_md5sum = None
    for line in run_command( 'md5sum %s' % filename , do_popen = True ).readlines() :
        gmn_md5sum = line.split()[0]
        return gmn_md5sum

class garmin_summary(object) :
    ''' summary class for a file '''
    def __init__( self , filename = '' , is_tcx = False , is_txt = False , md5sum = None ) :
        self.filename = filename
        self.begin_time = None
        self.begin_date = None
        self.sport = None
        self.total_calories = 0
        self.total_distance = 0
        self.total_duration = 0
        self.total_hr_dur = 0
        self.is_tcx = is_tcx
        self.is_txt = is_txt
        self.number_of_items = 0
        if md5sum :
            self.md5sum = md5sum
        elif self.filename != '' :
            self.md5sum = compute_file_md5sum( self.filename )

    def read_file( self ) :
        '''  read the file, calculate some stuff '''
        temp_gfile = garmin_file( self.filename )

        self.begin_time = temp_gfile.begin_time
        self.begin_date = temp_gfile.begin_date
        self.sport = temp_gfile.sport
        self.total_calories = temp_gfile.total_calories
        self.total_distance = temp_gfile.total_distance
        self.total_duration = temp_gfile.total_duration
        self.total_hr_dur = temp_gfile.total_hr_dur
        self.number_of_items += 1

        if self.total_calories == 0 and self.sport == 'running' and self.total_distance > 0.0 :
            self.total_calories = int( expected_calories( weight = 175 , pace_min_per_mile = ( self.total_duration / 60. ) / ( self.total_distance / meters_per_mile )  , distance = self.total_distance / meters_per_mile ) )
        elif self.total_calories == 0 and self.sport == 'stairs' and self.total_duration > 0 :
            self.total_calories = 325 * ( self.total_duration / 1100.89 )
        elif self.total_calories == 0 :
            return False
        if self.total_calories < 3 :
            return False
        if self.sport not in sport_types :
            print '%s not supported' % self.sport
            return False

        return True

    def add( self , summary_to_add ) :
        ''' add to totals '''
        self.total_calories += summary_to_add.total_calories
        self.total_distance += summary_to_add.total_distance
        self.total_duration += summary_to_add.total_duration
        if self.total_hr_dur > 0 and summary_to_add.total_hr_dur > 0 :
            self.total_hr_dur += summary_to_add.total_hr_dur
        elif self.total_hr_dur == 0 and summary_to_add.total_hr_dur > 0 :
            self.total_hr_dur = summary_to_add.total_hr_dur * ( self.total_duration / summary_to_add.total_duration )
        elif self.total_hr_dur > 0 and summary_to_add.total_hr_dur == 0 :
            self.total_hr_dur = self.total_hr_dur * self.total_duration / ( self.total_duration - summary_to_add.total_duration )
        else :
            self.total_hr_dur = 0
        self.number_of_items += 1

    def print_total_summary( self , sport = None , number_days = 0 , total_days = 0 ) :
        ''' print summary of total information '''
        print '%17s %10s \t %10s \t %10s \t' % ( ' ' , sport , '%4.2f mi' % ( self.total_distance/meters_per_mile ) , '%i cal' % self.total_calories ) ,

        if sport == 'running' or sport == 'walking' :
            print ' %10s \t' % ( '%s / mi' % print_h_m_s( self.total_duration / ( self.total_distance / meters_per_mile ) , False ) ) ,
            print ' %10s \t' % ( '%s / km' % print_h_m_s( self.total_duration / ( self.total_distance / 1000. ) , False ) ) ,
        elif sport == 'biking' :
            print ' %10s \t' % ( '%.2f mph' % ( ( self.total_distance / meters_per_mile ) / ( self.total_duration / 60. / 60. ) ) ) ,
        else :
            print ' %10s \t' % ' ' ,
        print ' %10s \t' % ( print_h_m_s( self.total_duration ) ),
        if self.total_hr_dur > 0 and sport != 'total' :
            print ' %7s %2s' % ( '%i bpm' % ( self.total_hr_dur / self.total_duration ) , ' ' ) ,
        else :
            print ' %7s %2s' % ( ' ' , ' ' ) ,
        if number_days > 0 and total_days > 0 :
            print '%16s' % ( '%i / %i days' % ( number_days , total_days ) )
        else :
            print ''
        return True

    def print_year_summary( self , sport = None , year = datetime.date.today().year , number_in_year = 0 ) :
        ''' print year summary information '''
        total_days = days_in_year( year )
        if datetime.datetime.today().year == year :
            total_days = ( datetime.datetime.today() - datetime.datetime( datetime.datetime.today().year , 1 , 1 ) ).days
        if sport == 'total' :
            print '%17s %10s \t %10s \t %10s \t' % ( year , sport , ' ' , '%i cal' % self.total_calories ) ,
        else :
            print '%17s %10s \t %10s \t %10s \t' % ( year , sport , '%4.2f mi' % ( self.total_distance/meters_per_mile ) , '%i cal' % self.total_calories ) ,
        if sport == 'running' or sport == 'walking' :
            print ' %10s \t' % ( '%s / mi' % print_h_m_s( self.total_duration / ( self.total_distance / meters_per_mile ) , False ) ) ,
            print ' %10s \t' % ( '%s / km' % print_h_m_s( self.total_duration / ( self.total_distance / 1000. ) , False ) ) ,
        elif sport == 'biking' :
            print ' %10s \t' % ( '%.2f mph' % ( ( self.total_distance / meters_per_mile ) / ( self.total_duration / 60. / 60. ) ) ) ,
        else :
            print ' %10s \t' % ' ' ,
        print ' %10s \t' % ( print_h_m_s( self.total_duration ) ),
        if self.total_hr_dur > 0 :
            print ' %7s %2s' % ( '%i bpm' % ( self.total_hr_dur / self.total_duration ) , ' ' ) ,
        else :
            print ' %7s %2s' % ( ' ' , ' ' ) ,
        print '%16s' % ( '%i / %i days' % ( number_in_year , total_days ) )
        return True

    def print_month_summary( self , sport = None , year = datetime.date.today().year , month = datetime.date.today().month , number_in_month = 0 ) :
        ''' print month summary information '''
        total_days = days_in_month( month = month , year = year )
        if datetime.datetime.today().year == year and datetime.datetime.today().month == month :
            total_days = ( datetime.datetime.today() - datetime.datetime( datetime.datetime.today().year , datetime.datetime.today().month , 1 ) ).days
        if sport == 'total' :
            print '%17s %10s \t %10s \t %10s \t' % ( '%i %s' % ( year , month_names[month-1] ) , sport , ' ' , '%i cal' % self.total_calories ) ,
        else :
            print '%17s %10s \t %10s \t %10s \t' % ( '%i %s' % ( year , month_names[month-1] ) , sport , '%4.2f mi' % ( self.total_distance/meters_per_mile ) , '%i cal' % self.total_calories ) ,
        if sport == 'running' or sport == 'walking' :
            print ' %10s \t' % ( '%s / mi' % print_h_m_s( self.total_duration / ( self.total_distance / meters_per_mile ) , False ) ) ,
            print ' %10s \t' % ( '%s / km' % print_h_m_s( self.total_duration / ( self.total_distance / 1000. ) , False ) ) ,
        elif sport == 'biking' :
            print ' %10s \t' % ( '%.2f mph' % ( ( self.total_distance / meters_per_mile ) / ( self.total_duration / 60. / 60. ) ) ) ,
        else :
            print ' %10s \t' % ' ' ,
        print ' %10s \t' % ( print_h_m_s( self.total_duration ) ),
        if self.total_hr_dur > 0 :
            print ' %7s %2s' % ( '%i bpm' % ( self.total_hr_dur / self.total_duration ) , ' ' ) ,
        else :
            print ' %7s %2s' % ( ' ' , ' ' ) ,
        print '%16s' % ( '%i / %i days' % ( number_in_month , total_days ) )
        return True

    def print_month_average( self , sport = None , number_of_months = 0 ) :
        ''' print month average information '''
        if number_of_months == 0 :
            return False
        if sport == 'total' :
            print '%17s %10s \t %10s \t %10s \t' % ( 'average / month' , sport , ' ' , '%i cal' % ( self.total_calories / number_of_months ) ) ,
        else :
            print '%17s %10s \t %10s \t %10s \t' % ( 'average / month' , sport , '%4.2f mi' % ( self.total_distance/meters_per_mile/number_of_months ) , '%i cal' % ( self.total_calories/number_of_months ) ) ,
        if sport == 'running' or sport == 'walking' :
            print ' %10s \t' % ( '%s / mi' % print_h_m_s( self.total_duration / ( self.total_distance / meters_per_mile ) , False ) ) ,
            print ' %10s \t' % ( '%s / km' % print_h_m_s( self.total_duration / ( self.total_distance / 1000. ) , False ) ) ,
        elif sport == 'biking' :
            print ' %10s \t' % ( '%.2f mph' % ( ( self.total_distance / meters_per_mile ) / ( self.total_duration / 60. / 60. ) ) ) ,
        else :
            print ' %10s \t' % ' ' ,
        print ' %10s \t' % ( print_h_m_s( self.total_duration/number_of_months ) ),
        if self.total_hr_dur > 0 :
            print ' %7s %2s' % ( '%i bpm' % ( self.total_hr_dur / self.total_duration ) , ' ' ) ,
        else :
            print ' %7s %2s' % ( ' ' , ' ' ) ,
        print ''
        return True

    def print_day_summary( self , sport = None , cur_date = datetime.date.today() ) :
        ''' print day summary information '''
        week = cur_date.isocalendar()[1]
        weekdayname = weekday_names[ cur_date.weekday() ]
        if sport == 'running' or sport == 'walking' :
            print '%17s %10s \t %10s \t %10s \t %10s \t %10s \t %10s' % ( '%10s %02i %3s' % ( cur_date , week , weekdayname ) , sport , '%.2f mi' % ( self.total_distance/meters_per_mile ) , '%i cal' % self.total_calories , '%s / mi' % print_h_m_s( self.total_duration / ( self.total_distance/meters_per_mile )  , False ) , '%s / km' % print_h_m_s( self.total_duration / ( self.total_distance/1000. )  , False ) , print_h_m_s( self.total_duration ) ) ,
        elif sport == 'biking' :
            print '%17s %10s \t %10s \t %10s \t %10s \t %10s' % ( '%10s %02i %3s' % ( cur_date , week , weekdayname ) , sport , '%.2f mi' % ( self.total_distance/meters_per_mile ) , '%i cal' % self.total_calories , '%.2f mph' % ( ( self.total_distance/meters_per_mile ) / ( self.total_duration/60./60. ) ) , print_h_m_s( self.total_duration ) ) ,
        else :
            print '%17s %10s \t %10s \t %10s \t %10s \t %10s' % ( '%10s %02i %3s' % ( cur_date , week , weekdayname ) , sport , '%.2f mi' % ( self.total_distance/meters_per_mile ) , '%i cal' % self.total_calories , ' ' , print_h_m_s( self.total_duration ) ) ,
        if self.total_hr_dur > 0 :
            print '\t %7s' % ( '%i bpm' % ( self.total_hr_dur / self.total_duration ) )
        else :
            print ''
        return True

    def print_day_average( self , sport = None , number_days = 0 ) :
        ''' print day average information '''
        if number_days == 0 :
            return False
        if sport == 'running' or sport == 'walking' :
            print '%17s %10s \t %10s \t %10s \t %10s \t %10s \t %10s' % ( 'average / day'  , sport , '%.2f mi' % ( self.total_distance/meters_per_mile/number_days ) , '%i cal' % ( self.total_calories/number_days ) , '%s / mi' % print_h_m_s( self.total_duration / ( self.total_distance/meters_per_mile )  , False ) , '%s / km' % print_h_m_s( self.total_duration / ( self.total_distance/1000. )  , False ) , print_h_m_s( self.total_duration/number_days ) ) ,
        elif sport == 'biking' :
            print '%17s %10s \t %10s \t %10s \t %10s \t %10s' % ( 'average / day' , sport , '%.2f mi' % ( self.total_distance/meters_per_mile/number_days ) , '%i cal' % ( self.total_calories/number_days ) , '%.2f mph' % ( ( self.total_distance/meters_per_mile ) / ( self.total_duration/60./60. ) ) , print_h_m_s( self.total_duration/number_days ) ) ,
        else :
            print '%17s %10s \t %10s \t %10s \t %10s \t %10s' % ( 'average / day' , sport , '%.2f mi' % ( self.total_distance/meters_per_mile/number_days ) , '%i cal' % ( self.total_calories/number_days ) , ' ' , print_h_m_s( self.total_duration/number_days ) ) ,
        if self.total_hr_dur > 0 :
            print '\t %7s' % ( '%i bpm' % ( self.total_hr_dur / self.total_duration ) )
        else :
            print ''
        return True

    def print_week_summary( self , sport = None , isoyear = None , isoweek = None , number_in_week = 0  , date = datetime.datetime.today() ) :
        ''' print week summary information '''
        if not isoyear :
            isoyear = date.isocalendar()[0]
        if not isoweek :
            isoweek = date.isocalendar()[1]
        if not number_in_week :
            number_in_week = self.number_of_items

        total_days = 7
        if datetime.datetime.today().isocalendar()[0] == isoyear and datetime.datetime.today().isocalendar()[1] == isoweek :
            total_days = datetime.datetime.today().isocalendar()[2]

        if sport == 'total' :
            print '%17s %10s \t %10s \t %10s \t' % ( '%i week %02i' % ( isoyear , isoweek ) , sport , ' ' , '%i cal' % self.total_calories ) ,
        else :
            print '%17s %10s \t %10s \t %10s \t' % ( '%i week %02i' % ( isoyear , isoweek ) , sport , '%4.2f mi' % ( self.total_distance/meters_per_mile ) , '%i cal' % self.total_calories ) ,

        if sport == 'running' or sport == 'walking' :
            print ' %10s \t' % ( '%s / mi' % print_h_m_s( self.total_duration / ( self.total_distance / meters_per_mile ) , False ) ) ,
            print ' %10s \t' % ( '%s / km' % print_h_m_s( self.total_duration / ( self.total_distance / 1000. ) , False ) ) ,
        elif sport == 'biking' :
            print ' %10s \t' % ( '%.2f mph' % ( ( self.total_distance / meters_per_mile ) / ( self.total_duration / 60. / 60. ) ) ) ,
        else :
            print ' %10s \t' % ' ' ,
        print ' %10s \t' % ( print_h_m_s( self.total_duration ) ),
        if self.total_hr_dur > 0 and sport != 'total' :
            print ' %7s %2s' % ( '%i bpm' % ( self.total_hr_dur / self.total_duration ) , ' ' ) ,
        else :
            print ' %7s %2s' % ( ' ' , ' ' ) ,
        print '%16s' % ( '%i / %i days' % ( number_in_week , total_days ) )
        return True

    def print_week_average( self , sport = None , number_days = 0 , number_of_weeks = 0 ) :
        ''' print week average information '''
        if number_of_weeks == 0 :
            return
        if sport == 'total' :
            print '%17s %10s \t %10s \t %10s \t' % ( 'avg / %3s weeks' % number_of_weeks , sport , ' ' , '%i cal' % ( self.total_calories/number_of_weeks ) ) ,
        else :
            print '%17s %10s \t %10s \t %10s \t' % ( 'avg / %3s weeks' % number_of_weeks , sport , '%4.2f mi' % ( self.total_distance/meters_per_mile/number_of_weeks ) , '%i cal' % ( self.total_calories/number_of_weeks ) ) ,

        if sport == 'running' or sport == 'walking' :
            print ' %10s \t' % ( '%s / mi' % print_h_m_s( self.total_duration / ( self.total_distance / meters_per_mile ) , False ) ) ,
            print ' %10s \t' % ( '%s / km' % print_h_m_s( self.total_duration / ( self.total_distance / 1000. ) , False ) ) ,
        elif sport == 'biking' :
            print ' %10s \t' % ( '%.2f mph' % ( ( self.total_distance / meters_per_mile ) / ( self.total_duration / 60. / 60. ) ) ) ,
        else :
            print ' %10s \t' % ' ' ,
        print ' %10s \t' % ( print_h_m_s( self.total_duration / number_of_weeks ) ),
        if self.total_hr_dur > 0 and sport != 'total' :
            print ' %7s %2s' % ( '%i bpm' % ( self.total_hr_dur / self.total_duration ) , ' ' ) ,
        else :
            print ' %7s %2s' % ( ' ' , ' ' ) ,
        print '%16s' % ( '%.1f / %i days' % ( float(number_days) / number_of_weeks , 7 ) )
        return True

def do_summary( directory , **options ) :
    ''' get summary of files in directory '''
    opts = [ 'do_plot' , 'do_year' , 'do_month' , 'do_week' , 'do_day' , 'do_file' , 'do_sport' , 'do_update' ]
    do_plot , do_year , do_month , do_week , do_day , do_file , do_sport , do_update = [ options[o] for o in opts ]
    
    pickle_file_is_modified = [ False ]
    file_vector = []
    filename_md5_dict = {}
    
    script_path = '/'.join( os.path.abspath( os.sys.argv[0] ).split('/')[:-1] )
    
    try :
        pkl_file = open( '%s/run/garmin.pkl' % script_path , 'rb' )
        filename_md5_dict = cPickle.load( pkl_file )
        pkl_file.close()
    except IOError :
        pass
    
    def add_file( gmn_filename ) :
        if not any( [ a in gmn_filename.lower() for a in [ '.gmn' , '.tcx' , '.fit' , '.txt' ] ] ) :
            return
        reduced_gmn_filename = gmn_filename.split('/')[-1]
        gmn_md5sum = compute_file_md5sum( gmn_filename )

        if ( reduced_gmn_filename not in filename_md5_dict ) or filename_md5_dict[reduced_gmn_filename].md5sum != gmn_md5sum or ( do_update and print_date_string( filename_md5_dict[reduced_gmn_filename].begin_time ) in list_of_corrected_laps ) :
            pickle_file_is_modified[0] = True
            gfile = garmin_summary( gmn_filename , md5sum = gmn_md5sum )
            if gfile.read_file() :
                filename_md5_dict[reduced_gmn_filename] = gfile
            else :
                print 'file %s not loaded for some reason' % reduced_gmn_filename
        else :
            gfile = filename_md5_dict[reduced_gmn_filename]
        file_vector.append( gfile )

    def process_files( arg , dirname , names ) :
        for name in names :
            gmn_filename = '%s/%s' % ( dirname , name )
            if os.path.isdir( gmn_filename ) :
                continue
            if '.pkl' in gmn_filename :
                continue
            add_file( gmn_filename )

    if type(directory) == str :
        if os.path.isdir( directory ) :
            os.path.walk( directory , process_files , None )
        elif os.path.isfile( directory ) :
            add_file( directory )
    if type(directory) == list :
        for d in directory :
            if os.path.isdir( d ) :
                os.path.walk( d , process_files , None )
            elif os.path.isfile( d ) :
                add_file( d )
            
    if pickle_file_is_modified[0] :
        pkl_file = open( '%s/run/garmin.pkl.tmp' % script_path , 'wb' )
        cPickle.dump( filename_md5_dict , pkl_file , cPickle.HIGHEST_PROTOCOL )
        pkl_file.close()
        run_command( 'mv %s/run/garmin.pkl.tmp %s/run/garmin.pkl' % ( script_path , script_path ) )

    if 'build' in options and options['build'] :
        return

    file_vector = sorted( file_vector , cmp = lambda x,y: cmp( x.begin_time , y.begin_time ) )

    year_set = set()
    month_set = set()
    week_set = set()
    day_set = set()
    sport_set = set()

    for gfile in file_vector :
        cur_date = gfile.begin_time.date()
        month_index = cur_date.year * 100 + cur_date.month
        week_index = cur_date.isocalendar()[0]*100 + cur_date.isocalendar()[1]
        if do_sport and do_sport not in gfile.sport :
            continue
        sport_set.add( gfile.sport )
        year_set.add( cur_date.year )
        month_set.add( month_index )
        week_set.add( week_index )
        day_set.add( cur_date )
    year_set = list(year_set)
    month_set = list(month_set)
    week_set = list(week_set)
    day_set = list(day_set)
    sport_set = list(sport_set)
    for item in year_set , month_set , week_set , day_set , sport_set :
        item.sort()

    total_sport_summary = {}
    year_sport_summary = {}
    month_sport_summary = {}
    day_sport_summary = {}
    week_sport_summary = {}

    total_sport_day_set = {}
    year_sport_day_set = {}
    month_sport_day_set = {}
    day_sport_set = {}
    week_sport_day_set = {}
    week_sport_set = {}

    for sport in sport_set :
        total_sport_summary[sport] = garmin_summary()
        total_sport_day_set[sport] = set()
        week_sport_set[sport] = set()
        for item in year_sport_summary , month_sport_summary , day_sport_summary , week_sport_summary , year_sport_day_set , month_sport_day_set , day_sport_set , week_sport_day_set :
            item[sport] = {}
        for year in year_set :
            year_sport_summary[sport][year] = garmin_summary()
            year_sport_day_set[sport][year] = set()
        for month in month_set :
            month_sport_summary[sport][month] = garmin_summary()
            month_sport_day_set[sport][month] = set()
        for day in day_set :
            day_sport_summary[sport][day] = garmin_summary()
            day_sport_set[sport] = set()
        for week in week_set :
            week_sport_summary[sport][week] = garmin_summary()
            week_sport_day_set[sport][week] = set()

    total_summary = garmin_summary()
    year_summary = {}
    month_summary = {}
    day_summary = {}
    week_summary = {}

    year_day_set = {}
    month_day_set = {}
    week_day_set = {}

    for year in year_set :
        year_summary[year] = garmin_summary()
        year_day_set[year] = set()
    for month in month_set :
        month_summary[month] = garmin_summary()
        month_day_set[month] = set()
    for day in day_set :
        day_summary[day] = garmin_summary()
    for week in week_set :
        week_summary[week] = garmin_summary()
        week_day_set[week] = set()

    for gfile in file_vector :
        cur_date = gfile.begin_time.date()
        month_index = cur_date.year * 100 + cur_date.month
        week_index = cur_date.isocalendar()[0]*100 + cur_date.isocalendar()[1]
        sport = gfile.sport
        if do_sport and do_sport not in gfile.sport :
            continue
        year = cur_date.year
        total_sport_summary[sport].add( gfile )
        total_sport_day_set[sport].add( cur_date )
        total_summary.add( gfile )
        year_sport_summary[sport][year].add( gfile )
        year_sport_day_set[sport][year].add( cur_date )
        year_summary[year].add( gfile )
        year_day_set[year].add( cur_date )
        month_sport_summary[sport][month_index].add( gfile )
        month_sport_day_set[sport][month_index].add( cur_date )
        month_summary[month_index].add( gfile )
        month_day_set[month_index].add( cur_date )
        day_sport_summary[sport][cur_date].add( gfile )
        day_sport_set[sport].add( cur_date )
        day_summary[cur_date].add( gfile )
        week_sport_summary[sport][week_index].add( gfile )
        week_sport_day_set[sport][week_index].add( cur_date )
        week_sport_set[sport].add( week_index )
        week_summary[week_index].add( gfile )
        week_day_set[week_index].add( cur_date )

    ### If more than one year, default to year-to-year summary
    print ''
    if do_file :
        for sport in sport_types :
            if sport not in sport_set :
                continue
            for gfile in file_vector :
                cur_date = gfile.begin_time.date()
                if gfile.sport != sport :
                    continue
                gfile.print_day_summary( sport , cur_date )
            print ''
        print ''
    if do_day :
        for sport in sport_types :
            if sport not in sport_set :
                continue
            for cur_date in day_set :
                if cur_date not in day_sport_set[sport] :
                    continue
                day_sport_summary[sport][cur_date].print_day_summary( sport , cur_date )
            print ''
            if not do_sport :
                total_sport_summary[sport].print_day_average( sport , len(day_sport_set[sport]) )
                print ''
        if not do_sport :
            for cur_date in day_set :
                day_summary[cur_date].print_day_summary( 'total' , cur_date )
            print ''
        if not do_sport :
            total_summary.print_day_average( 'total' , len(day_set) )
            print ''
    if do_week :
        for sport in sport_types :
            if sport not in sport_set :
                continue
            for yearweek in week_set :
                if len(week_sport_day_set[sport][yearweek]) == 0 :
                    continue
                isoyear = int(yearweek/100)
                isoweek = yearweek % 100
                week_sport_summary[sport][yearweek].print_week_summary( sport , isoyear , isoweek , len(week_sport_day_set[sport][yearweek]) )
            print ''
            if not do_sport :
                total_sport_summary[sport].print_week_average( sport = sport , number_days = len(total_sport_day_set[sport]) , number_of_weeks = len(week_sport_set[sport]) )
                print ''
        for yearweek in week_set :
            isoyear = int(yearweek/100)
            isoweek = yearweek % 100
            if not do_sport :
                week_summary[yearweek].print_week_summary( 'total' , isoyear , isoweek , len(week_day_set[yearweek]) )
        if not do_sport :
            print ''
            total_summary.print_week_average( sport = 'total' , number_days = len(day_set) , number_of_weeks = len(week_set) )
            print ''
    if do_month :
        for sport in sport_types :
            if sport not in sport_set :
                continue
            for yearmonth in month_set :
                year = int( yearmonth / 100 )
                month = yearmonth % 100
                if len(month_sport_day_set[sport][yearmonth]) == 0 :
                    continue
                month_sport_summary[sport][yearmonth].print_month_summary( sport , year , month , len(month_sport_day_set[sport][yearmonth]) )
            print ''
            if not do_sport :
                total_sport_summary[sport].print_month_average( sport , number_of_months = len(month_sport_day_set[sport]) )
                print ''
        print ''
        for yearmonth in month_set :
            year = int( yearmonth / 100 )
            month = yearmonth % 100
            if len(month_day_set[yearmonth]) == 0 :
                continue
            if not do_sport :
                month_summary[yearmonth].print_month_summary( 'total' , year , month , len(month_day_set[yearmonth]) )
        print ''
        if not do_sport :
            total_summary.print_month_average( sport = 'total' , number_of_months = len(month_set) )
            print ''
    if do_year :
        for sport in sport_types :
            if sport not in sport_set :
                continue
            for year in year_set :
                if len(year_sport_day_set[sport][year]) == 0 :
                    continue
                year_sport_summary[sport][year].print_year_summary( sport , year , len(year_sport_day_set[sport][year]) )
            print ''
        print ''
        for year in year_set :
            if len(year_day_set[year]) == 0 :
                continue
            if not do_sport : year_summary[year].print_year_summary( 'total' , year , len(year_day_set[year]) )
        print ''

    for sport in sport_types :
        if sport not in sport_set :
            continue
        if len(total_sport_day_set[sport]) > 1 and not do_day :
            total_sport_summary[sport].print_day_average( sport , len(day_sport_set[sport]) )
    if not do_sport :
        print ''
        total_summary.print_day_average( 'total' , len(day_set) )
        print ''
    for sport in sport_types :
        if sport not in sport_set :
            continue
        if len(week_sport_set[sport]) > 1 and not do_week :
            total_sport_summary[sport].print_week_average( sport = sport , number_days = len(total_sport_day_set[sport]) , number_of_weeks = len(week_sport_set[sport]) )
    if not do_sport :
        print ''
        total_summary.print_week_average( 'total' , number_days = len(day_set) , number_of_weeks = len(week_set) )
        print ''
    for sport in sport_types :
        if sport not in sport_set :
            continue
        if len(month_sport_day_set[sport]) > 1 and not do_month:
            total_sport_summary[sport].print_month_average( sport , number_of_months = len(month_sport_day_set[sport]) )
    if not do_sport :
        print ''
        total_summary.print_month_average( 'total' , number_of_months = len(month_set) )
        print ''
    begin_date = day_set[0]
    end_date = day_set[-1]
    total_days = ( end_date - begin_date ).days
    for sport in sport_types :
        if sport not in sport_set :
            continue
        if len(total_sport_day_set[sport]) == 0 :
            continue
        if not do_sport :
            total_sport_summary[sport].print_total_summary( sport , len(total_sport_day_set[sport]) , total_days )
    if not do_sport :
        print ''
        total_summary.print_total_summary( 'total' , len(day_set) , total_days )
        print ''

    if 'occur' in options :
        occur_map = {}
        for i in range(0,len(day_set)+1) :
            occur_map[i] = 0

        if len(day_set) > 1 :
            last_date = day_set[0]
            for i in range(1,len(day_set)) :
                if (day_set[i]-day_set[i-1]).days > 1 :
                    occur_map[(day_set[i-1] - last_date).days + 1] += 1
                    if ( (day_set[i-1] - last_date).days + 1 ) > 5 :
                        print day_set[i-1]
                    last_date = day_set[i]
            try :
                occur_map[(day_set[-1]-last_date).days + 1] += 1
            except KeyError :
                print day_set[-1] , last_date
                print (day_set[-1]-last_date).days + 1
                print occur_map
                print day_set
                print 'key error'
                exit(1)

            if not do_sport :
                for i in range(0,len(day_set)+1) :
                    if occur_map[i] > 0 :
                        print i , occur_map[i]
