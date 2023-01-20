#!/usr/bin/env python3

import os
import sys
from lsl.common.stations import parse_ssmif


def main(args):
    ssmifname = args[0]
    station = parse_ssmif(ssmifname)
    nant = len(station.antennas) // 2
    
    bad = []
    for i in range(nant):
        a = station.antennas[2*i]
        for j in range(i+1, nant):
            b = station.antennas[2*j]
            if a.arx.id != b.arx.id:
                continue
                
            if (a.arx.channel-1)//4 == (b.arx.channel-1)//4:
                bad.append([f"LWA{a.stand.id:03d}", f"LWA{b.stand.id:03d}"])
    print(bad)

if __name__ == '__main__':
    main(sys.argv[1:])
