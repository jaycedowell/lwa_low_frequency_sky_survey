#!/usr/bin/env python3

import os
import sys
from astropy.io import fits as astrofits
from astropy.table import Table as AstroTable
from reproject import reproject_to_healpix


def main(args):
    for filename in args:
        ## Load in the data and trim off the degenerate axes
        hdu = astrofits.open(filename)
        hdr = hdu[0].header
        hdr['NAXIS'] = 2
        for axis in (3, 4):
            for key in ('NAXIS', 'CTYPE', 'CRPIX', 'CRVAL', 'CDELT', 'CUNIT'):
                if key[0] == 'C':
                    altkey = key.replace('C', 'O')
                    hdr[f"{altkey}{axis}"] = hdr[f"{key}{axis}"]
                del hdr[f"{key}{axis}"]
        data = hdu[0].data[0,0,...]
        hdu.close()
        
        # Reproject to HEALpix
        hpx, _ = reproject_to_healpix((data, hdr), 'icrs', order='nearest-neighbor', nested=False, nside=256)
        
        # Save the HEALpix data to FITS
        t = AstroTable()
        t['flux'] = hpx
        t.meta['ORDERING'] = 'RING'
        t.meta['COORDSYS'] = 'E'
        t.meta['NSIDE'] = 256
        t.meta['INDXSCHM'] = 'IMPLICIT'
        for key in ('TELESCOP', 'OBSERVER', 'OBJECT', 'ORIGIN', 'DATE-OBS', 'EQUINOX', 'SPECSYS'):
            t.meta[key] = hdr[key]
        for key in hdr.keys():
            if key[:3] == 'WSC':
                t.meta[key] = hdr[key]
            elif key[:1] == 'O':
                t.meta[key] = hdr[key]
                
        outname = os.path.basename(filename)
        outname, _ = os.path.splitext(outname)
        outname += '_healpix.fits'
        t.write(outname)


if __name__ == '__main__':
    main(sys.argv[1:])
