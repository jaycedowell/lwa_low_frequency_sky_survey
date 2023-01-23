#!/usr/bin/env python3

import os
import sys
import numpy as np
from casacore.tables import table

from matplotlib import pyplot as plt


def main(args):
    filename = args[0]
    tb = table(filename, ack=False)
    ant = tb.getcol('ANTENNA1')
    dly = tb.getcol('FPARAM')
    wgt = tb.getcol('SNR')
    tb.close()
    
    fig = plt.figure()
    ax = fig.gca()
    ax.scatter(ant, dly[:,0,0], marker='o')
    ax.set_xlabel('Antenna Number')
    ax.set_ylabel('Delay [ns]')
    plt.show()


if __name__ == '__main__':
    main(sys.argv[1:])
