#!/usr/bin/env casa

"""
Given a collection of CASA measurement sets that are near transit of a calibrator,
concatenate the files together to get ready for self-cal.
"""

import os
import sys

args = sys.argv[3:]
if args[0][-4:] == '.txt':
    ## File list - load and replace args
    with open(args[0], 'r') as fh:
        filelist = fh.read()
    args = filelist.split('\n')
    if args[-1] == '':
        args = args[:-1]
        
to_combine = []
for filename in args:
    if filename[-1] == '/':
        filename = filename[:-1]
    if filename[-3:] != '.ms':
        continue
    to_combine.append(filename)
    
outname = os.path.basename(to_combine[0])
outname = outname.split('_', 1)[0]
outname = outname+'_transit.ms'
concat(to_combine, outname)
flagmanager(outname)
