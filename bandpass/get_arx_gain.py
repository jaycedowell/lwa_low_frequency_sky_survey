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
    mean_resp = []
    for a in station.antennas:
        if a.combined_status != 33:
            continue
            
        freq, resp = a.arx.response('full', dB=False)
        mean_resp.append(resp)
    mean_resp = np.array(mean_resp)
    mean_resp = np.mean(mean_resp, axis=0)
    
    with open('mean_arx_gain.txt', 'w') as fh:
        fh.write("# Freq    Gain\n")
        for f,r in zip(freq, mean_resp):
            fh.write("%f  %f\n" % (f, r))


if __name__ == '__main__':
    main(sys.argv[1:])
