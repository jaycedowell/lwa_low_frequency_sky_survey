#!/usr/bin/env python3

"""
Given a collection of CASA measurement sets, create flags to each one.  Flags
are created by smoothing the mean auto-correlation data and looking for peaks in
the raw/smoothed ratio.
"""

import os
import sys
import numpy as np
from scipy.signal import savgol_filter
from casacore.tables import table

from matplotlib import pyplot as plt


def flag(spec, chan_win=19, grow=True):
    spec = 10*np.log10(spec)
    
    smooth = savgol_filter(spec, chan_win, 3)
    diff = spec - smooth
    mean = diff.mean()
    std = diff.std()
    
    bad = np.where(np.abs(diff - mean)/std > 1.75)[0]
    if grow:
        new_bad = []
        for b in bad:
            new_bad.extend([b-1, b, b+1])
        new_bad = list(set(new_bad))
        if new_bad[0] < 0:
            new_bad = new_bad[1:]
        if new_bad[-1] == spec.size:
            new_bad = new_bad[:-1]
        bad = new_bad
        
    return bad


def main(args):
    # Initial file type check
    if args[0][-4:] == '.txt':
        ## File list - load and replace args
        with open(args[0], 'r') as fh:
            filelist = fh.read()
        args = filelist.split('\n')
        if args[-1] == '':
            args = args[:-1]
            
    # Load the data
    for filename in args:
        tb = table(filename, ack=False)
        autos = tb.query('ANTENNA1 == ANTENNA2')
        try:
            data = autos.getcol('CORRECTED_DATA')
        except RuntimeError:
            data = autos.getcol('DATA')
            
        # complex vis -> power -> XX+YY -> median
        data = np.abs(data)
        data = data[...,0] + data[...,1]
        data = np.median(data, axis=0)
        
        # Flag
        bad = flag(data)
        bad.extend(list(range(50)))
        bad.sort()
        
        # # Plots
        # fig = plt.figure()
        # ax = fig.gca()
        # ax.plot(10*np.log10(data))
        # data[bad] = np.nan
        # ax.plot(10*np.log10(data))
        # plt.show()
        
        # Save
        outname = os.path.basename(filename)
        outname, _ = os.path.splitext(outname)
        outname += '_channel_flags.txt'
        with open(outname, 'w') as fh:
            fh.write(','.join([str(b) for b in bad]))
            
        tb.close()

if __name__ == '__main__':
    main(sys.argv[1:])
