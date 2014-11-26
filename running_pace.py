#!/usr/bin/python

import os
import numpy as np
import matplotlib
matplotlib.use( 'Agg' )
import matplotlib.pyplot as plt
import scipy.optimize as optimize
from util import print_h_m_s , print_m_s

def lin_func( x , *p ) :
    return p[0] + p[1] * x + p[2] * x**2

def pow_func( x , *p ) :
    return p[0] * x**p[1]

def do_fit( data , func , p0 ) :
    datax = data[:,0]
    datay = data[:,1]
    p , c = optimize.curve_fit( func , datax , datay , p0 = p0 )
    l , v = np.linalg.eig( c )
    sig = v.dot( np.sqrt( np.diag( l ) ) ).dot( v.T )
    dp = np.sqrt( np.sum( sig.dot( v )**2 , axis=0 ) )
    
    errfunc = lambda p, x, y: func(x,*p) - y
    
    residuals = errfunc( p, datax, datay)
    s_res = np.std(residuals)
    ps = []
    datayerrors = None
    # 100 random data sets are generated and fitted
    for _ in range(100):
      if datayerrors is None:
          randomDelta = np.random.normal(0., s_res, len(datay))
          randomdataY = datay + randomDelta
      else:
          randomDelta =  np.array( [ \
                             np.random.normal(0., derr,1)[0] \
                             for derr in datayerrors ] )
          randomdataY = datay + randomDelta
      randomfit, randomcov = \
          optimize.leastsq( errfunc, p0, args=(datax, randomdataY),\
                            full_output=0)
      ps.append( randomfit )

    ps = np.array(ps)
    mean_pfit = np.mean(ps,0)
    Nsigma = 1. # 1sigma gets approximately the same as methods above
                # 1sigma corresponds to 68.3% confidence interval
                # 2sigma corresponds to 95.44% confidence interval
    err_pfit = Nsigma * np.std(ps,0)

    pfit_bootstrap = mean_pfit
    perr_bootstrap = err_pfit
    
    # return p , dp
    return pfit_bootstrap , perr_bootstrap

def read_result_file( fname ) :
    running_paces = []
    f = open( fname , 'r' )
    for line in f :
        e = line.split()
        dist_meters = float(e[0])
        pace_minute = int(e[1])
        pace_second = int(e[2])
        race_year = int(e[3])
        include_race = int(e[4])
        race_name = ' '.join( e[5:] )
        t = ( pace_minute + pace_second/60. )
        if include_race :
            running_paces.append( [ dist_meters , t ] )
    
    rp = np.array( running_paces )
    p , dp = do_fit( rp , lin_func , p0 = [ 1 , 1 , 1 ] )
    pp , pm = p+dp , p-dp
    plt.scatter( rp[:,0] , rp[:,1] )
    plt.xlim( [0,60] )
    plt.ylim( [0,16] )

    x = np.linspace( 0 , 60 , 100 )
    plt.plot( x , lin_func( x , *p ) , 'r' , linewidth=2.5)
    plt.plot( x , lin_func( x , *pp ) , 'r--' )
    plt.plot( x , lin_func( x , *pm ) , 'r--' )

    p , dp = do_fit( rp , pow_func , p0 = [ 0.5 , 0.5 ] )
    pp , pm = p+dp , p-dp
    plt.plot( x , pow_func( x , *p ) , 'b' , linewidth=2.5)
    plt.plot( x , pow_func( x , *pp ) , 'b--' )
    plt.plot( x , pow_func( x , *pm ) , 'b--' )

    plt.savefig('running_pace.png')

if __name__ == '__main__' :
    read_result_file( 'running_paces.txt' )
