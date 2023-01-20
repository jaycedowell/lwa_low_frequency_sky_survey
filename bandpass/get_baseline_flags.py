#!/usr/bin/env python3

"""
Given a LWA1 SSMIF file, find all signals on the same output RJ45 connector and
create a flag file containing those baselines.
"""

import os
import sys
from lsl.common.stations import parse_ssmif


def main(args):
    # Load the SSMIF
    ssmifname = args[0]
    station = parse_ssmif(ssmifname)
    nant = len(station.antennas) // 2
    
    # Find bad baselines and save by name
    bad = []
    for i in range(nant):
        a = station.antennas[2*i]
        for j in range(i+1, nant):
            b = station.antennas[2*j]
            if a.arx.id != b.arx.id:
                continue
                
            if (a.arx.channel-1)//4 == (b.arx.channel-1)//4:
                bad.append(f"LWA{a.stand.id:03d}~LWA{b.stand.id:03d}")
                
    # Write to disk
    with open('baseline_flags.txt', 'w') as fh:
        fh.write(','.join(bad))


if __name__ == '__main__':
    main(sys.argv[1:])
