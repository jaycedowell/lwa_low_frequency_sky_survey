#!/usr/bin/env casa

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
    calname = os.path.basename(filename)
    calname, _ = os.path.splitext(calname)
    calname = calname+'_two_pt.dcal'
    
    try:
        shutil.rmtree(calname)
    except OSError:
        pass
        
    clearcal(filename, addmodel=True)
    ft(filename, complist='two_pt_model.cl', usescratch=True)
    gaincal(filename, calname, refant='LWA151', combine='obs,scan,field', solint='inf', solnorm=False, gaintype='K', calmode='p')
