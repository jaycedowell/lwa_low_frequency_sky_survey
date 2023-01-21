#!/usr/bin/env python3

"""
Given a collection of .npz files from stationMaster.py, average all together in
time and come up with a set of good/bad/suspect flags that can be used to update
the SSMIF.
"""

import os
import sys
import numpy as np

from matplotlib import pyplot as plt


def flag(spec, median_spec, chans=[1066,3552]):
    """
    Given a stand/pol x channel array of data and a median spectrum, create a
    set of good/bad flags for each antenna.
    """
    
    nchan = chans[1] - chans[0]
    spec = 10*np.log10(spec[:,chans[0]:chans[1]])
    median_spec = 10*np.log10(median_spec[chans[0]:chans[1]])
    
    status = [3,]*spec.shape[0]
    for i in range(spec.shape[0]):
        # Flag the channel for that stand if it is more than 3 dB off the median
        bad = np.where(np.abs(spec[i,:] - median_spec) > 3)[0]
        if len(bad) > 0.25*nchan:
            status[i] = 1
        spec[i,bad] = np.nan
        
        # If the flattened spectrum deviates by more than 1.75 sigma, flag the channel
        # spec[i,:] -= median_spec
        # mean = np.nanmean(spec[i,:])
        # std = np.nanstd(spec[i,:])
        # 
        # bad = np.where((np.abs(spec[i,:]) - mean)/std > 1.75)[0]
        # if len(bad) > 0.1*nchan:
        #     if status[i] == 3:
        #         status[i] = 2
                
    return status


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
        data = np.load(filename)
        freq, spec = data['freq'][...], data['masterSpectra'][0,...]
        try:
            mean_spec += spec
        except NameError:
            mean_spec = spec*1.0
        data.close()
        
    # Compute the median spectrum
    spec = mean_spec / len(args)
    med = np.median(spec, axis=0)
    
    # Flag
    status = flag(spec, med)
    
    # Flag pairs where one element is bad
    for i in range(0, len(status), 2):
        sx = status[i+0]
        sy = status[i+1]
        if sx != 3 or sy != 3:
            status[i+0] = min([status[i+0], 2])
            status[i+1] = min([status[i+1], 2])
            
    # Report
    print('  Good:   ', len(list(filter(lambda x: x == 3, status))))
    print('  Suspect:', len(list(filter(lambda x: x == 2, status))))
    print('  Bad:    ', len(list(filter(lambda x: x == 1, status))))
    
    # Plots
    fig = plt.figure()
    ax = fig.gca()
    ax.plot(freq[1:]/1e6, 10*np.log10(med[1:]))
    ax.set_title('Median')
    plt.draw()
    
    for s in (3, 2, 1):
        fig = plt.figure()
        ax = fig.gca()
        for i,l in enumerate(status):
            if l != s:
                continue
            ax.plot(freq[1:]/1e6, 10*np.log10(spec[i,1:]))
        ax.set_title(f"Status: {s}")
        plt.draw()
    plt.show()
    
    # Final file
    with open('antenna_flags.txt', 'w') as fh:
        for i,l in enumerate(status):
            if l != 3:
                fh.write(f"{i},")


if __name__ == '__main__':
    main(sys.argv[1:])
