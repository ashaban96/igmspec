""" Module to ingest COS-Dwarfs

Bordoloi et al. 201X
"""
from __future__ import print_function, absolute_import, division, unicode_literals


import numpy as np
import pdb
import warnings
import os, json, glob, imp

from astropy.table import Table, Column, vstack
from astropy.coordinates import SkyCoord, match_coordinates_sky
from astropy import units as u
from astropy.time import Time

from linetools.spectra import io as lsio
from linetools import utils as ltu

from pyigm.cgm.cos_halos import COSDwarfs

from igmspec.ingest import utils as iiu

#igms_path = imp.find_module('igmspec')[1]


def grab_meta():
    """ Grab COS-Dwarfs meta table
    Returns
    -------

    """
    cosdwarfs = COSDwarfs()
    cosdwarfs.load_sys(tfile=cosdwarfs.cdir+'/cos-dwarfs_systems.v1.1.tar.gz', chk_lowz=False)

    # Coord
    lst = [getattr(cgm_abs.igm_sys, 'coord') for cgm_abs in cosdwarfs.cgm_abs]
    ra = [coord.ra.value for coord in lst]
    dec = [coord.dec.value for coord in lst]

    cdwarfs_meta = Table()
    cdwarfs_meta['RA'] = ra
    cdwarfs_meta['DEC'] = dec
    cdwarfs_meta['DATE-OBS'] = '1999-9-9'
    # RA/DEC, DATE
    # Others
    cdwarfs_meta.add_column(Column(['G130M/G160M']*len(cdwarfs_meta), name='GRATING'))
    cdwarfs_meta.add_column(Column([20000.]*len(cdwarfs_meta), name='R'))
    cdwarfs_meta.add_column(Column([2000.]*len(cdwarfs_meta), name='EPOCH'))
    cdwarfs_meta['INSTR'] = 'COS' # Deals with padding
    cdwarfs_meta['TELESCOPE'] = 'HST'
    cdwarfs_meta['zem'] = cosdwarfs.zem
    cdwarfs_meta['sig_zem'] = 0.  # Need to add
    cdwarfs_meta['flag_zem'] = 'SDSS'
    # Done
    return cdwarfs_meta


def meta_for_build():
    """ Generates the meta data needed for the IGMSpec build
    Returns
    -------
    meta : Table
    """
    cdwarfs_meta = grab_meta()
    #
    meta = Table()
    for key in ['RA', 'DEC', 'zem', 'sig_zem', 'flag_zem']:
        meta[key] = cdwarfs_meta[key]
    meta['STYPE'] = str('QSO')
    # Return
    return meta


def hdf5_adddata(hdf, IDs, sname, debug=False, chk_meta_only=False,
                 mk_test_file=False):
    """ Append COS-Dwarfs data to the h5 file

    Parameters
    ----------
    hdf : hdf5 pointer
    IDs : ndarray
      int array of IGM_ID values in mainDB
    sname : str
      Survey name
    chk_meta_only : bool, optional
      Only check meta file;  will not write
    mk_test_file : bool, optional
      Generate the debug test file for Travis??

    Returns
    -------

    """
    # Add Survey
    print("Adding {:s} survey to DB".format(sname))
    cdwarfs_grp = hdf.create_group(sname)
    # Load up
    meta = grab_meta()
    bmeta = meta_for_build()
    # Checks
    if sname != 'COS-Dwarfs':
        raise IOError("Not expecting this survey..")
    if np.sum(IDs < 0) > 0:
        raise ValueError("Bad ID values")
    # Open Meta tables
    if len(bmeta) != len(IDs):
        raise ValueError("Wrong sized table..")

    # Generate ID array from RA/DEC
    c_cut = SkyCoord(ra=bmeta['RA'], dec=bmeta['DEC'], unit='deg')
    c_all = SkyCoord(ra=meta['RA'], dec=meta['DEC'], unit='deg')
    # Find new sources
    idx, d2d, d3d = match_coordinates_sky(c_all, c_cut, nthneighbor=1)
    if np.sum(d2d > 0.1*u.arcsec):
        raise ValueError("Bad matches in COS-Dwarfs")
    meta_IDs = IDs[idx]

    # Loop me to bid the full survey catalog
    meta.add_column(Column(meta_IDs, name='IGM_ID'))

    # Build spectra (and parse for meta)
    nspec = len(meta)
    max_npix = 20000  # Just needs to be large enough
    data = np.ma.empty((1,),
                       dtype=[(str('wave'), 'float64', (max_npix)),
                              (str('flux'), 'float32', (max_npix)),
                              (str('sig'),  'float32', (max_npix)),
                              #(str('co'),   'float32', (max_npix)),
                             ])
    # Init
    spec_set = hdf[sname].create_dataset('spec', data=data, chunks=True,
                                         maxshape=(None,), compression='gzip')
    spec_set.resize((nspec,))
    wvminlist = []
    wvmaxlist = []
    npixlist = []
    speclist = []
    # Loop
    path = os.getenv('RAW_IGMSPEC')+'/COS-Dwarfs/'
    maxpix = 0
    for jj,row in enumerate(meta):
        # Generate full file
        coord = ltu.radec_to_coord((row['RA'],row['DEC']))
        full_file = path+'/J{:s}{:s}_nbin3_coadd.fits.gz'.format(coord.ra.to_string(unit=u.hour,sep='',pad=True)[0:4],
                                           coord.dec.to_string(sep='',pad=True,alwayssign=True)[0:5])
        if 'J1051-0051' in full_file:
            full_file = path+'/PG1049-005_nbin3_coadd.fits.gz'
        if 'J1204+2754' in full_file:
            full_file = path+'/PG1202+281_nbin3_coadd.fits.gz'
        # Parse name
        fname = full_file.split('/')[-1]
        # Extract
        print("COS-Dwarfs: Reading {:s}".format(full_file))
        spec = lsio.readspec(full_file)
        # npix
        npix = spec.npix
        if npix > max_npix:
            raise ValueError("Not enough pixels in the data... ({:d})".format(npix))
        else:
            maxpix = max(npix,maxpix)
        # Some fiddling about
        for key in ['wave','flux','sig']:
            data[key] = 0.  # Important to init (for compression too)
        data['flux'][0][:npix] = spec.flux.value
        data['sig'][0][:npix] = spec.sig.value
        data['wave'][0][:npix] = spec.wavelength.value
        # Meta
        speclist.append(str(fname))
        wvminlist.append(np.min(data['wave'][0][:npix]))
        wvmaxlist.append(np.max(data['wave'][0][:npix]))
        npixlist.append(npix)
        if chk_meta_only:
            continue
        # Only way to set the dataset correctly
        spec_set[jj] = data

    #
    print("Max pix = {:d}".format(maxpix))
    # Add columns
    meta.add_column(Column(speclist, name='SPEC_FILE'))
    meta.add_column(Column(npixlist, name='NPIX'))
    meta.add_column(Column(wvminlist, name='WV_MIN'))
    meta.add_column(Column(wvmaxlist, name='WV_MAX'))
    meta.add_column(Column(np.arange(nspec,dtype=int), name='SURVEY_ID'))

    # Add HDLLS meta to hdf5
    if iiu.chk_meta(meta):
        if chk_meta_only:
            pdb.set_trace()
        hdf[sname]['meta'] = meta
    else:
        raise ValueError("meta file failed")
    # References
    refs = [dict(url='http://adsabs.harvard.edu/abs/2014ApJ...796..136B',
                 bib='bordoloi+14'),
            ]
    jrefs = ltu.jsonify(refs)
    hdf[sname]['meta'].attrs['Refs'] = json.dumps(jrefs)
    #
    return

