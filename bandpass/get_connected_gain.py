#!/usr/bin/env python3

import os
import sys
import glob
import gzip
import numpy as np
from scipy.optimize import minimize

from lsl import astro
from lsl.common.stations import lwa1
from lsl.common.progress import ProgressBarPlus

from matplotlib import pyplot as plt


def load_wx(filename):
    """
    Given a wxview database backup file, parse the file and return a three-
    element tuple of:
     * Unix timestamp (UTC)
     * indoor temperature (C)
     * outdoor temperature (C)
    """
    
    dt, temp_in, temp_out = [], [], []
    with gzip.open(filename , 'r') as fh:
        for line in fh:
            line = line.decode()
            if not line.startswith('INSERT INTO'):
                continue
                
            line = line.split('(', 1)[-1]
            fields = line.split(',')
            try:
                temp_in.append(float(fields[6]))
                temp_out.append(float(fields[7]))
                dt.append(float(fields[0]))
            except ValueError:
                continue
                
    return dt, temp_in, temp_out


def load_arx(filename):
    """
    Given a ARX temperature log file, parse the file and return a two-element
    tuple of:
     * Unix timestamp (UTC)
     * mean subsystem temperature (C)
    """
    
    dt, temp = [], []
    with gzip.open(filename, 'r') as fh:
        for line in fh:
            line = line.decode()
            fields = line.split(',', 4)
            fields = [float(f) for f in fields]
            dt.append(fields[0])
            temp.append(sum(fields[1:])/4.0)
    return dt, temp


def main(args):
    # Get an observer so we know what the LST is
    obs = lwa1.get_observer()

    # Load in the weather station data
    wx_dt, wx_temp_in, wx_temp_out = load_wx('wview_backup_151116.gz')
    wx_dt = np.array(wx_dt)
    wx_temp_in = np.array(wx_temp_in)
    wx_temp_out = np.array(wx_temp_out)
    
    # Load in the ARX temperatures
    arx_dt, arx_temp = [], []
    for filename in glob.glob('temp_19*.gz'):
        dt, temp = load_arx(filename)
        arx_dt.extend(dt)
        arx_temp.extend(temp)
    arx_dt = np.array(arx_dt)
    arx_temp = np.array(arx_temp)
    order = np.argsort(arx_dt)
    arx_dt = arx_dt[order]
    arx_temp = arx_temp[order]
    
    # Load in the data
    pb = ProgressBarPlus(max=len(args))
    sys.stdout.write(pb.show()+'\r')
    sys.stdout.flush()
    
    mjd, temp_in, temp_out, lst, med_power = [], [], [], [], []
    for filename in args:
        ## Open the file and pull out the data - we'll save the MJD
        data = np.load(filename)
        obsdate = data['date'].item().decode().replace('-', '/')
        mjd.append(obsdate.split(None, 1)[0])
        
        ## Compute the LST
        obs.date = obsdate
        lst.append(obs.sidereal_time())
        
        ## Get the outdoor temperatures for this file
        unix_dt = astro.utcjd_to_unix(obs.date+astro.DJD_OFFSET)
        closest = np.argmin(np.abs(unix_dt-wx_dt))
        temp_out.append(wx_temp_out[closest])
        
        ## Get the ARX temperature for this file
        closest = np.argmin(np.abs(unix_dt-arx_dt))
        temp_in.append(arx_temp[closest])
        
        ## Pull out the median power
        try:
            freq_range
        except NameError:
            freq = data['freq']
            freq_range = np.where((freq>40e6) & (freq<70e6))[0]
        
        power = data['masterSpectra'][0,...]
        power = np.median(power[:,freq_range])
        med_power.append(power)
        
        data.close()
        
        pb.inc()
        sys.stdout.write(pb.show()+'\r')
        sys.stdout.flush()
        
    sys.stdout.write(pb.show()+'\r')
    sys.stdout.write('\n')
    sys.stdout.flush()
    
    # Run the tempeture vs gain fit - joint indoor (ARX)/outdoor
    mjd = np.array(mjd)
    temp_in = np.array(temp_in)
    temp_out = np.array(temp_out)
    lst = np.array(lst)
    med_power = np.array(med_power)
    orig_power = med_power*1.0
    gain_corrs = np.ones(mjd.size)
    
    delta_ts_in, delta_ts_out, ratios = [], [], []
    for i in range(mjd.size):
        valid = np.where((np.abs(lst-lst[i]) < 600/86400*2*np.pi) & (lst != lst[i]))[0]
        if len(valid) < 2:
            continue
            
        delta_t_in = temp_in[valid] - temp_in[i]
        delta_t_out = temp_out[valid] - temp_out[i]
        power_ratio = med_power[valid] / med_power[i]
        
        delta_ts_in.extend(list(delta_t_in))
        delta_ts_out.extend(list(delta_t_out))
        ratios.extend(list(power_ratio))
        
    delta_ts_in = np.array(delta_ts_in)
    delta_ts_out = np.array(delta_ts_out)
    ratios = np.array(ratios)
    
    def plane(params, x, y):
        a, b, c = params
        return a*x + b*y + c
        
    def plane_err(params, x, y, z):
        return ((z - plane(params, x, y))**2).sum()
        
    def fmin(params, tin=delta_ts_in, tout=delta_ts_out, r=ratios):
        return plane_err(params, tin, tout, r)
        
    temp_gain_fit0 = [0, 0, 0]
    temp_gain_fit = minimize(fmin, temp_gain_fit0)
    temp_gain_fit = [temp_gain_fit.x[i] for i in range(3)]
    
    # Save the corrections/apply the correcitons
    gain_corrs /= plane(temp_gain_fit, temp_in-temp_in[0], temp_out-temp_out[0])
    med_power /= plane(temp_gain_fit, temp_in-temp_in[0], temp_out-temp_out[0])
    
    # The temperature fit doesn't remove all of the variation between runs.  Use
    # the overlap in LST between consecutive runs to further pin down the gain
    # corrections
    unique_mjd = np.unique(mjd)
    scount = 0 
    scales = [1,]
    for i,m in enumerate(unique_mjd):
        ## Find all files associated with this run
        m_valid = np.where(mjd == m)[0]
        m_lst = lst[m_valid]
        
        ## If it looks like we are in a situaiton where we wrap around at 24h, 
        ## shift the LSTs by 12 h
        if m_lst.max() - m_lst.min() > np.pi:
            print('!!! shift !!!')
            scount += 1
            lst += np.pi
            lst %= 2*np.pi
            m_lst = lst[m_valid]
            
        ## Pull out the overlaps with the next run
        j = (i + 1) % len(unique_mjd)
        o = unique_mjd[j]
        o_valid = np.where((mjd == o) & (lst >= m_lst.min()) & (lst <= m_lst.max()))[0]
        if len(o_valid) > 15:
            ### Good overlap - trim down the overlap region from the original "m" run
            print(m, '<>', o, '@', len(o_valid), 'with', np.min(m_lst))
            o_lst = lst[o_valid]
            o_power = np.median(med_power[o_valid])
            
            m_valid = np.where((mjd == m) & (lst >= o_lst.min()) & (lst <= o_lst.max()))[0]
            m_power = np.median(med_power[m_valid])
            
            ### Compute the scale factor and apply them to the "o" run
            scale = m_power / o_power
            scales.append(scale)
            print('=>', scale, '&', scales[-1])

            o_valid = np.where(mjd == o)[0]
            med_power[o_valid] *= scale
            
    # Deal with any LST shifting we may have done
    scount %= 2
    lst += np.pi*scount
    lst %= 2*np.pi
    
    # Update the global gain corrections to include these residual corrections
    # determined from the overlap regions
    for m,s in zip(unique_mjd, scales):
        valid = np.where(mjd == m)[0]
        gain_corrs[valid] *= s
        
    # Save the gain corrections
    for filename,gaincorr in zip(args, gain_corrs):
        outname = os.path.basename(filename)
        outname, _ = os.path.splitext(outname)
        outname += '_gain_corr.txt'
        with open(outname, 'w') as fh:
            fh.write(str(gaincorr))
            
    # Check that we have kept everything straight by applying the corrections
    # in bulk and generating a plot
    fixed_power = orig_power*gain_corrs
    
    fig = plt.figure()
    ax = fig.gca()
    unique_mjd = np.unique(mjd)
    for m in unique_mjd:
        valid = np.where(mjd == m)[0]
        sub_lst = lst[valid]*12/np.pi
        sub_orig = orig_power[valid]
        sub_fixed = fixed_power[valid]
        
        if sub_lst.max() - sub_lst.min() > 12:
            lst_diff = np.abs(np.diff(sub_lst))
            bad = np.where(lst_diff > 1)[0][0] + 1
            
            sub_lst = np.insert(sub_lst, bad, np.nan)
            sub_orig = np.insert(sub_orig, bad, np.nan)
            sub_fixed = np.insert(sub_fixed, bad, np.nan)
            
        ax.plot(sub_lst, sub_orig, alpha=0.4)
        ax.plot(sub_lst, sub_fixed)
    ax.set_xlabel('LST [hr]')
    ax.set_ylabel('Mean Power [arb]')
    plt.draw()
    plt.show()


if __name__ == '__main__':
    main(sys.argv[1:])
