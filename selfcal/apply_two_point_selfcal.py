#!/usr/bin/env python3

"""
Given .dcal and .gcal files from two_point_selfcal.py and a collection of CASA
measurement sets, apply the gain and delay calibration to each measurement set.
"""

import os
import sys
import numpy as np
from casacore.tables import table


def load_dcal(filename):
    """
    Load in the delays from a .dcal measurement set and return a two-element
    tuple of antennas and delays (in ns).
    """
    
    tb = table(filename, ack=False)
    ant = tb.getcol('ANTENNA1')[...]
    dly = tb.getcol('FPARAM')[...]
    tb.close()
    
    return ant, dly


def load_gcal(filename):
    """
    Load in the gains from a .gcal measurement set and return a two-element
    tuple of antennas and gains.
    
    .. note:: For any antennas without valid gain solutions, the mean gain value
              of all valid antennas is used.
    """
    
    tb = table(filename, ack=False)
    ant = tb.getcol('ANTENNA1')[...]
    gai = np.abs(tb.getcol('CPARAM')[...])
    flg = tb.getcol('FLAG')
    tb.close()
    
    good = np.where(flg == 0)
    bad = np.where(flg == 1)
    mean = np.mean(gai[good])
    gai[bad] = mean
    
    return ant, gai


def main(args):
    calname = args[0]
    dcalname = calname.replace('.gcal', '.dcal')
    gcalname = calname.replace('.dcal', '.gcal')
    dant, dly = load_dcal(dcalname)
    gant, gai = load_gcal(gcalname)
    
    # Load the data
    for filename in args[1:]:
        ## Get the frequency range of the file
        tb = table(os.path.join(filename, 'SPECTRAL_WINDOW'), ack=False)
        freq = np.array([], dtype=np.float64)
        for freqIF in tb.col('CHAN_FREQ'):
            freq = np.concatenate([freq, freqIF])
        tb.close()
        
        ## Load in the actual data
        tb = table(filename, readonly=False, ack=False)
        ant1 = tb.getcol('ANTENNA1')
        ant2 = tb.getcol('ANTENNA2')
        data = tb.getcol('DATA')
        
        ## Apply the corrections to the data
        for i in range(ant1.size):
            ### Delay
            v1 = np.where(dant == ant1[i])[0]
            v2 = np.where(dant == ant2[i])[0]
            
            data[i,:,0] /= np.exp(2j*np.pi*(freq/1e9*(dly[v1,0,0]-dly[v2,0,0])))
            data[i,:,1] /= np.exp(2j*np.pi*(freq/1e9*(dly[v1,0,1]-dly[v2,0,1])))
            
            #### Gain
            #v1 = np.where(gant == ant1[i])[0]
            #v2 = np.where(gant == ant2[i])[0]
            #
            #data[i,:,0] /= gai[v1,0,0]*gai[v2,0,0]
            #data[i,:,1] /= gai[v1,0,1]*gai[v2,0,1]
            
        ## Save back to DATA
        tb.putcol('DATA', data)
        tb.close()


if __name__ == '__main__':
    main(sys.argv[1:])
