#!/usr/bin/env python3

import os
import sys

from lsl.common.stations import parse_ssmif


def main(args):
    flagname = args[0]
    ssmifname = args[1]
    
    with open(flagname, 'r') as fh:
        flags = fh.read()
    flags = flags.split(',')
    if flags[-1] == '':
        flags = flags[:-1]
    print(f"Loaded {len(flags)} antenna flags")
    
    in_ant_stat = False
    outname = os.path.basename(ssmifname)
    outname, outext = os.path.splitext(outname)
    outname = outname+'_UPDATED'+outext
    with open(outname, 'w') as oh:
        with open(ssmifname, 'r') as fh:
            for line in fh:
                if line.startswith('ANT_STAT['):
                    in_ant_stat = True
                    continue
                    
                if in_ant_stat and line[0] in (' ', '\t', '\n', '#'):
                    in_ant_stat = False
                    oh.write("Auto-generated flags\n")
                    for flag in flags:
                        oh.write(f"ANT_STAT[{int(flag)+1}]  1\n")
                oh.write(line)


if __name__ == '__main__':
    main(sys.argv[1:])
