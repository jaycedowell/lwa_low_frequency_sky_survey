#!/usr/bin/env python3

import os
import sys
import glob
import numpy as np
import subprocess


def main(args):
    # Gather up the list of antenna and FEE files to use
    ant_measurements = glob.glob('./Antenna_Impedance/Data/LWA1/Antenna-Antenna/*.s2p')
    fee_measurements = glob.glob('./Antenna_Impedance/Data/FEE_Bulk_Measurements/S2P/*.s2p')
    
    # Process NS and EW separately
    for side in ('A', 'B'):
        cmd = [sys.executable, './Antenna_Impedance/compute_IMF.py', '-n', '-s', '-a']
        cmd.extend(ant_measurements)
        cmd.append('--')
        cmd.extend(list(filter(lambda x: x.find(f"-{side}_") != -1, fee_measurements)))
        subprocess.check_call(cmd)
        
    # Get the mean FEE gain
    gain0 = np.loadtxt('FEE_Gain_NS.txt')
    gain1 = np.loadtxt('FEE_Gain_EW.txt')
    freq, g0, g1 = gain0[:,0], gain0[:,3], gain1[:,3]
    mean_gain = (g0 + g1) / 2
    valid = np.where(freq <= 100e6)[0]
    with open('mean_fee_gain.txt', 'w') as fh:
        fh.write("# Freq    Gain\n")
        for f,g in zip(freq[valid], mean_gain[valid]):
            fh.write("%f  %f\n" % (f, g))
            
    # Get the mean impedance mismatch factor
    imf0 = np.loadtxt('IMF_NS.txt')
    imf1 = np.loadtxt('IMF_EW.txt')
    freq, f0, f1 = imf0[:,0], imf0[:,3], imf1[:,3]
    mean_imf = (f0 + f1) / 2
    valid = np.where(freq <= 100e6)[0]
    with open('mean_fee_ant_imf.txt', 'w') as fh:
        fh.write("# Freq    IMF\n")
        for f,g in zip(freq[valid], mean_imf[valid]):
            fh.write("%f  %f\n" % (f, g))
            
    # Cleanup
    for filename in ('FEE_Gain_EW.txt', 'FEE_Gain_NS.txt', 'IMF_EW.txt', 'IMF_NS.txt'):
        try:
            os.remove(filename)
        except OSError:
            pass


if __name__ == '__main__':
    main(sys.argv[1:])
