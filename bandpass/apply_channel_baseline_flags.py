#!/usr/bin/env casa

"""
Given a collection of CASA measurement sets, apply flags from get_channel_flags.py
and get_baseline_flags.py to the data using CASA's `flagdata` task.
"""

import os
import sys

args = sys.argv[1:]
if args[0][-4:] == '.txt':
    ## File list - load and replace args
    with open(args[0], 'r') as fh:
        filelist = fh.read()
    args = filelist.split('\n')
    if args[-1] == '':
        args = args[:-1]
        
for filename in args:
    if filename[-1] == '/':
        filename = filename[:-1]
    if filename[-3:] != '.ms':
        continue
    flagname = os.path.basename(filename)
    flagname, _ = os.path.splitext(flagname)
    flagname = flagname+'_channel_flags.txt'
    if os.path.exists(flagname):
        with open(flagname, 'r') as fh:
            flagcmd = fh.read()
        flagdata(vis=filename, mode='manual', spw=flagcmd)
    else:
        print("No channel flags for %s" % filename)
        
    flagname = 'baseline_flags.txt'
    if os.path.exists(flagname):
        with open(flagname, 'r') as fh:
            flagcmd = fh.read()
        flagdata(vis=filename, mode='manual', antenna=flagcmd)
    else:
        print("No baselines flags for %s" % filename)
