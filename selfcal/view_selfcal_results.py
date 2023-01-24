#!/usr/bin/env python3

"""
Visualize the delays in a .dcal measurement set created by two_point_selfcal.py
"""

import os
import sys
import numpy as np
from casacore.tables import table

from matplotlib import pyplot as plt


def main(args):
    filename = args[0]
    dcalname = filename.replace('.gcal', '.dcal')
    gcalname = filename.replace('.dcal', '.gcal')
    
    tb = table(dcalname, ack=False)
    ant = tb.getcol('ANTENNA1')
    dly = tb.getcol('FPARAM')
    wgt = tb.getcol('SNR')
    tb.close()
    
    tb = table(gcalname, ack=False)
    ant = tb.getcol('ANTENNA1')
    gai = np.abs(tb.getcol('CPARAM'))
    flg = tb.getcol('FLAG')
    wgt = tb.getcol('SNR')
    tb.close()
    
    good = np.where(flg == 0)
    bad = np.where(flg == 1)
    mean = np.mean(gai[good])
    gai[bad] = mean
    
    fig = plt.figure()
    ax = fig.gca()
    ax.scatter(ant, dly[:,0,0], marker='o', label='X')
    ax.scatter(ant, dly[:,0,1], marker='o', label='Y')
    ax.set_xlabel('Antenna Number')
    ax.set_ylabel('Delay [ns]')
    fig.legend(loc=0)
    plt.draw()
    
    fig = plt.figure()
    ax = fig.gca()
    ax.scatter(ant, gai[:,0,0], marker='o', label='X')
    ax.scatter(ant, gai[:,0,1], marker='o', label='Y')
    ax.set_xlabel('Antenna Number')
    ax.set_ylabel('Gain [arb]')
    fig.legend(loc=0)
    plt.draw()
    
    plt.show()


if __name__ == '__main__':
    main(sys.argv[1:])
