#!/usr/bin/env python3

import os
import sys
import numpy as np

from lsl.common.stations import parse_ssmif


def main(args):
    # Load in the SSMIF
    ssmifname = args[0]
    station = parse_ssmif(ssmifname)
    
    # Compute the mean ARX response for all good dipoles
    for a in station.antennas:
        if a.status != 33:
            continue
            
        freq, resp = a.arx.response('full', dB=False)
        try:
            mean_resp += resp
            count_resp += 1
        except NameError:
            mean_resp = resp
            count_resp = 1
    mean_resp /= count_resp
    
    with open('mean_arx_gain.txt', 'r') as fh:
        fh.write("# Freq    Gain\n")
        for f,r in zip(freq, mean_resp):
            fh.write("%f  %f\n" % (f, r))


if __name__ == '__main__':
    main(sys.argv[1:])
