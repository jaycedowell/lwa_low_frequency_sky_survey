#!/usr/bin/env python3

"""
Given a collection of CASA measurement sets, apply bandpass corrections to the
data.  These include:
 * the FEE gain (get_front_end_terms.py)
 * the FEE-antenna mismatch factor (get_front_end_terms.py)
 * the response of the analog receivers (get_arx_gain.py)
 * the temperature-dependent gains (get_connected_gain.py)
"""

import os
import sys
import numpy as np
from casacore.tables import table
from scipy.interpolate import interp1d


def main(args):
    # Initial file type check
    if args[0][-4:] == '.txt':
        ## File list - load and replace args
        with open(args[0], 'r') as fh:
            filelist = fh.read()
        args = filelist.split('\n')
        if args[-1] == '':
            args = args[:-1]
            
    # Load in the antenna independent corrections...
    fee = np.loadtxt('mean_fee_gain.txt')
    imf = np.loadtxt('mean_fee_ant_imf.txt')
    arx = np.loadtxt('mean_arx_gain.txt')
    
    # And convert them to interpolators
    fee = interp1d(fee[:,0], fee[:,1])
    imf = interp1d(imf[:,0], imf[:,1])
    arx = interp1d(arx[:,0], arx[:,1])
    
    # Load the data
    for filename in args:
        ## Load in the observation-based gain correction
        corrname = os.path.basename(filename)
        corrname, _ = corrname.splitext(corrname)
        corrname += '_gain_corr.txt'
        if os.path.exists(corrname):
            with open(corrname, 'r') as fh:
                corr = float(fh.read())
        else:
            print("No temperature-based gain correction for %s" % filename)
            corr = 1.0
            
        ## Get the frequency range of the file
        tb = table(os.path.join(filename, 'SPECTRAL_WINDOW'), ack=False)
        freq = np.array([], dtype=np.float64)
        for freqIF in tb.col('CHAN_FREQ'):
            freq = np.concatenate([freq, freqIF])
        tb.close()
        
        ## Get the total per-channel correction for the data
        corr = corr / fee(freq) / imf(freq) / arx(freq)
        corr.shape = (1,)+corr.shape+(1,)
        
        ## Load in the actual data and apply the corrections
        tb = table(filename, readonly=False, ack=False)
        data = tb.getcol('DATA')
        data *= corr
        
        ## Save back to DATA
        tb.putcol('DATA', data)
        tb.close()


if __name__ == '__main__':
    main(sys.argv[1:])
