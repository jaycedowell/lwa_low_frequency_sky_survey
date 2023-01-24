#!/usr/bin/env casa

"""
Give a CASA measurement set created by combine_transit_data.py, run delay-only
and amplitude-only self calibration on the data using a two point sky model
consisting of CygA and CasA.
"""

import os
import sys
import shutil

args = sys.argv[3:]
if args[0][-4:] == '.txt':
    ## File list - load and replace args
    with open(args[0], 'r') as fh:
        filelist = fh.read()
    args = filelist.split('\n')
    if args[-1] == '':
        args = args[:-1]

# Initial two-source model
cl.done()
try:
    shutil.rmtree('two_pt_model.cl')
except OSError:
    pass
cl.addcomponent(flux=16530, dir='J2000 23h23m24s +58d48m54s', index=-0.72, spectrumtype='spectral index', freq='80MHz', label='CasA')
cl.addcomponent(flux=16300, dir='J2000 19h59m28.35663s +40d44m02.0970s', index=-0.58, spectrumtype='spectral index', freq='80MHz', label='CygA')
cl.rename('two_pt_model.cl')
cl.done()

for filename in args:
    if filename[-1] == '/':
        filename = filename[:-1]
    if filename[-3:] != '.ms':
        continue
        
    # Delay calibration
    dcalname = os.path.basename(filename)
    dcalname, _ = os.path.splitext(dcalname)
    dcalname = dcalname+'_two_pt.dcal'
    
    try:
        shutil.rmtree(dcalname)
    except OSError:
        pass
        
    clearcal(filename, addmodel=True)
    ft(filename, complist='two_pt_model.cl', usescratch=True)
    gaincal(filename, dcalname,  refant='LWA151', combine='obs,scan,field', solint='inf', solnorm=False, gaintype='K', calmode='p')
    
    # Amplitude calibration
    gcalname = os.path.basename(filename)
    gcalname, _ = os.path.splitext(gcalname)
    gcalname = gcalname+'_two_pt.gcal'
    
    try:
        shutil.rmtree(gcalname)
    except OSError:
        pass
        
    gaincal(filename, gcalname,  refant='LWA151', combine='obs,scan,field', solint='inf', solnorm=False, gaintype='G', calmode='a')
