#!/usr/bin/env python3

import os
import sys
import numpy as np

from astropy.io import fits as astrofits
from astropy.table import Table as AstroTable


def main(args):
    dataXX, wgtXX = [], []
    dataYY, wgtYY = [], []
    for filename in args:
        print(filename)
        shortname = os.path.basename(filename)
        if shortname.find('healwgt') != -1:
            continue
        pol = 'XX' if shortname.find('XX') != -1 else 'YY'
        
        hdu = astrofits.open(filename, mode='readonly')
        image = np.array(hdu[1].data['flux'][...])
        hdu.close()
        
        hdu = astrofits.open(filename.replace('healpix', 'healwgt'), mode='readonly')
        weight =  np.array(hdu[1].data['flux'][...])
        hdu.close()
        
        if pol == 'XX':
            dataXX.append(image)
            wgtXX.append(weight)
        else:
            dataYY.append(image)
            wgtYY.append(weight)
            
    dataXX, wgtXX = np.array(dataXX), np.array(wgtXX)
    dataYY, wgtYY = np.array(dataYY), np.array(wgtYY)
    print(dataXX.shape, dataXX.dtype, wgtXX.shape, wgtXX.dtype)
    
    invalid = np.where((wgtXX < 0.1))# & (wgtYY < 0.1))
    dataXX[invalid] = np.nan
    # dataYY[invalid] = np.nan
    
    dataXX /= wgtXX
    # dataYY /= wgtYY
    data = dataXX# + dataYY
    
    med = np.nanmedian(data, axis=0)
    std = np.nanstd(data, axis=0)
    
    t = AstroTable()
    t['flux'] = med
    t.meta['ORDERING'] = 'RING'
    t.meta['COORDSYS'] = 'E'
    t.meta['NSIDE'] = 256
    t.meta['INDXSCHM'] = 'IMPLICIT'
    t.write('final.fits')
    
    t = AstroTable()
    t['flux'] = std
    t.meta['ORDERING'] = 'RING'
    t.meta['COORDSYS'] = 'E'
    t.meta['NSIDE'] = 256
    t.meta['INDXSCHM'] = 'IMPLICIT'
    t.write('weight.fits')


if __name__ == '__main__':
    main(sys.argv[1:])
