#!/usr/bin/env python3

"""
Given a collection of *_healpix.fits files from `convert_to_healpix.py`, mosaic
the images together and write out a final image.
"""

import os
import re
import sys
import numpy as np

from astropy.io import fits as astrofits
from astropy.table import Table as AstroTable

from lsl.common.progress import ProgressBarPlus


# RegEx to match image names
_FREQ_RE = re.compile(r'(?P<mjd>\d{6})_\d{9}_(?P<freq>\d{1,2})MHz-(?P<pol>[XY][XY])-image_healpix.fits')


def main(args):
    # Make sure we only have data for a single frequency
    freqs = []
    count = 0
    for filename in args:
        mtch = _FREQ_RE.search(filename)
        if mtch is not None:
            freq = int(mtch.group('freq'))
            if freq not in freqs:
                freqs.append(freq)
            count += 1
    if len(freqs) > 1:
        raise RuntimeError(f"ERROR: Found data for {len(freqs)} frequencies")
    print(f"Working on {count} files at {freqs[0]} MHz")
    
    # Load the data
    pb = ProgressBarPlus(max=count)
    sys.stdout.write(pb.show()+'\r')
    sys.stdout.flush()
    
    dataXX, wgtXX = [], []
    dataYY, wgtYY = [], []
    for filename in args:
        shortname = os.path.basename(filename)
        if shortname.find('healwgt') != -1:
            continue
        pol = 'XX' if shortname.find('XX') != -1 else 'YY'
        
        ## The image
        hdu = astrofits.open(filename, mode='readonly')
        image = np.array(hdu[1].data['flux'][...])
        hdu.close()
        
        ## The weights
        hdu = astrofits.open(filename.replace('healpix', 'healwgt'), mode='readonly')
        weight =  np.array(hdu[1].data['flux'][...])
        hdu.close()
        
        if pol == 'XX':
            dataXX.append(image)
            wgtXX.append(weight)
        else:
            dataYY.append(image)
            wgtYY.append(weight)
            
        pb.inc()
        sys.stdout.write(pb.show()+'\r')
        sys.stdout.flush()
        
    sys.stdout.write(pb.show()+'\r')
    sys.stdout.write('\n')
    sys.stdout.flush()
    
    # Warn the user if we only find one polarization
    if len(dataXX) == 0:
        print("WARNING: No data loaded for XX")
    if len(dataYY) == 0:
        print("WARNING: No data loaded for YY")
        
    print("Building mosaic")
    
    # Convert to a numpy array and make out low weight pixels
    dataXX, wgtXX = np.array(dataXX), np.array(wgtXX)
    dataYY, wgtYY = np.array(dataYY), np.array(wgtYY)
    print(dataXX.shape, dataXX.dtype, wgtXX.shape, wgtXX.dtype)
    
    invalid = np.where((wgtXX < 0.1))
    dataXX[invalid] = np.nan
    wgtXX[invalid] = np.nan
    # invalud = np.where((wgtYY < 0.1))
    # dataYY[invalid] = np.nan
    # wgtYY[invalid] = np.nan
    
    # Correct for the beam pattern
    dataXX /= wgtXX
    # dataYY /= wgtYY
    
    # Weighted mean of the data - XX and YY jointly
    # Based on Case I of https://seismo.berkeley.edu/~kirchner/Toolkits/Toolkit_12.pdf
    ## Weight function
    wfunc = lambda x: x
    
    num = np.nansum(dataXX*wfunc(wgtXX), axis=0)# + np.nansum(dataYY*wfunc(wgtYY), axis=0)
    den = np.nansum(wfunc(wgtXX), axis=0)# + np.nansum(wfunc(wgtYY), axis=0)
    image = num/den
    good_count = len(np.where(np.isfinite(image))[0])
    print(f"Weighted mean determined for {good_count} pixels ({100.0*good_count/image.size:.1f}% of the sky)")
    
    # Uncertainty
    ## Effective degrees of freedom
    num = (np.nansum(wfunc(wgtXX), axis=0))**2# + np.nansum(wfunc(wgtXX), axis=0))**2
    den = np.nansum(wfunc(wgtXX)**2, axis=0)# + np.nansum(wfunc(wgtXX)**2, axis=0)
    n_eff = num/den
    print(f"Effective degrees-of-freedom range from {np.nanmin(n_eff):.0f} to {np.nanmax(n_eff):.0f}")
    
    ## Variance
    num = np.nansum(wfunc(wgtXX)*(dataXX - image)**2, axis=0)# + np.nansum(wfunc(wgtYY)*(dataYY - image)**2, axis=0)
    den = np.nansum(wfunc(wgtXX), axis=0)# + np.nansum(wfunc(wgtYY), axis=0)
    variance = num/den * n_eff/(n_eff-1)
    
    ## Weight - the standard error on the mean
    weight = np.sqrt(variance / n_eff)
    
    outname = f"combined_{freqs[0]}MHz_healpix.fits"
    weightname = outname.replace('_healpix.fits', '_healwgt.fits')
    print(f"Saving to {outname}")
    t = AstroTable()
    t['flux'] = image
    t.meta['ORDERING'] = 'RING'
    t.meta['COORDSYS'] = 'E'
    t.meta['NSIDE'] = 256
    t.meta['INDXSCHM'] = 'IMPLICIT'
    t.write(outname)
    
    t = AstroTable()
    t['flux'] = weight
    t.meta['ORDERING'] = 'RING'
    t.meta['COORDSYS'] = 'E'
    t.meta['NSIDE'] = 256
    t.meta['INDXSCHM'] = 'IMPLICIT'
    t.write(weightname)


if __name__ == '__main__':
    main(sys.argv[1:])
