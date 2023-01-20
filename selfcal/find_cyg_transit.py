#!/usr/bin/env python3

"""
Given a collection of CASA measurement sets, calculate the elevation of CygA
above the horizon and keep only files where that value is >81 degees.
"""

import os
import sys
import ephem
from casacore.tables import table

from lsl import astro
from lsl.common.stations import lwa1


def main(args):
    # Initial file type check
    if args[0][-4:] == '.txt':
        ## File list - load and replace args
        with open(args[0], 'r') as fh:
            filelist = fh.read()
        args = filelist.split('\n')
        if args[-1] == '':
            args = args[:-1]
            
    # Get CygA
    cyg = ephem.readdb("CygA,f|J,19:59:28.30,+40:44:02.0,1")
    
    # Get an observer
    obs = lwa1.get_observer()
    
    # Load the data
    transit_data = {}
    for filename in args:
        ## Get the date of observation
        tb = table(filename, ack=False)
        t = tb.getcell('TIME_CENTROID', 0)
        mjd = t/86400
        
        # Find out where CygA is in the sky.  If it is >81 degrees elevation, 
        # save it
        obs.date = mjd + (astro.MJD_OFFSET - astro.DJD_OFFSET)
        cyg.compute(obs)
        if cyg.alt > ephem.degrees('81:00:00'):
            try:
                transit_data[int(mjd)].append(filename)
            except KeyError:
                transit_data[int(mjd)] = [filename,]
                
        tb.close()
        
    # Save outputs
    for mjd in transit_data:
        dataname = f"cyg_transit_{mjd:06d}.txt"
        with open(dataname, 'w') as fh:
            for filename in transit_data[mjd]:
                fh.write(filename+'\n')


if __name__ == '__main__':
    main(sys.argv[1:])
