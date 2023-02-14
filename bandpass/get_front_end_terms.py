#!/usr/bin/env python3

"""
Use data from https://github.com/cdilullo/Antenna_Impedance to calculate band-
pass corrections for the FEE gain and the FEE-antenna impedeance mismatch factor.
"""

import os
import sys
import glob
import numpy as np
import subprocess


def main(args):
    # Gather up the list of antenna and FEE files to use
    ant_measurements = glob.glob('./Antenna_Impedance/Data/LWA1/Dipole-Dipole/*.s2p')
    fee_measurements = glob.glob('./Antenna_Impedance/Data/FEE/*/*')

    # Process NS and EW separately
    for side, output in zip(('A', 'B'), ('FEE_S11_NS.npz', 'FEE_S11_EW.npz')):
        # This command makes the FEE ouput .npz files with S11
        cmd = [sys.executable, './Antenna_Impedance/Data/FEE/read_FEE_S_params.py', '-n', '-s']
        cmd.extend(list(filter(lambda x: x.find(f"-{side}_") != -1, fee_measurements)))
        subprocess.check_call(cmd)

        # This command reads in the output files along with the single antenna measurments
        # to compute the IMF correction
        cmd = [sys.executable, './Antenna_Impedance/compute_IMF.py', '-n', '-s']
        cmd.extend(output)
        cmd.append('--')
        cmd.extend(list(filter(lambda x: x.find(f"-{side}_") != -1, ant_measurements)))
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
