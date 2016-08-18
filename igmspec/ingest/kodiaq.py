""" Module to ingest KODIAQ Survey data

O'Meara et al. 2016
"""
from __future__ import print_function, absolute_import, division, unicode_literals


import numpy as np
import pdb
import os, json
import imp

import datetime

from astropy.table import Table, Column
from astropy.coordinates import SkyCoord, match_coordinates_sky
from astropy import units as u
from astropy.io import fits

from linetools import utils as ltu
from linetools.spectra import io as lsio

from igmspec.ingest import utils as iiu

igms_path = imp.find_module('igmspec')[1]


def grab_meta():
    """ Grab KODIAQ meta Table
    Returns
    -------

    """
    kodiaq_file = igms_path+'/data/meta/KODIAQ_DR1_summary.ascii'
    kodiaq_meta = Table.read(kodiaq_file, format='ascii', comment='#')
    nspec = len(kodiaq_meta)
    # Verify DR1
    for row in kodiaq_meta:
        assert row['kodrelease'] == 1
    # RA/DEC, DATE
    ra = []
    dec = []
    dateobs = []
    for row in kodiaq_meta:
        # Fix DEC
        # Get RA/DEC
        coord = ltu.radec_to_coord((row['sRA'],row['sDEC']))
        ra.append(coord.ra.value)
        dec.append(coord.dec.value)
        # DATE
        dvals = row['pi_date'].split('_')
        tymd = str('{:s}-{:s}-{:02d}'.format(dvals[-1],dvals[1][0:3],int(dvals[2])))
        tval = datetime.datetime.strptime(tymd, '%Y-%b-%d')
        dateobs.append(datetime.datetime.strftime(tval,'%Y-%m-%d'))
    kodiaq_meta.add_column(Column(ra, name='RA'))
    kodiaq_meta.add_column(Column(dec, name='DEC'))
    kodiaq_meta.add_column(Column(dateobs, name='DATE-OBS'))
    #
    kodiaq_meta.add_column(Column(['HIRES']*nspec, name='INSTR'))
    kodiaq_meta.add_column(Column(['Keck-I']*nspec, name='TELESCOPE'))
    #
    return kodiaq_meta


def meta_for_build():
    """ Generates the meta data needed for the IGMSpec build
    Returns
    -------
    meta : Table
    """
    kodiaq_meta = grab_meta()
    # Cut down to unique QSOs
    names = np.array([name[0:26] for name in kodiaq_meta['qso']])
    uni, uni_idx = np.unique(names, return_index=True)
    kodiaq_meta = kodiaq_meta[uni_idx]
    nqso = len(kodiaq_meta)
    #
    meta = Table()
    meta['RA'] = kodiaq_meta['RA']
    meta['DEC'] = kodiaq_meta['DEC']
    meta['zem'] = kodiaq_meta['zem']
    meta['sig_zem'] = [0.]*nqso
    meta['flag_zem'] = [str('SIMBAD')]*nqso
    meta['STYPE'] = [str('QSO')]*nqso
    # Return
    return meta


def hdf5_adddata(hdf, IDs, sname, debug=False, chk_meta_only=False):
    """ Append KODIAQ data to the h5 file

    Parameters
    ----------
    hdf : hdf5 pointer
    IDs : ndarray
      int array of IGM_ID values in mainDB
    sname : str
      Survey name
    chk_meta_only : bool, optional
      Only check meta file;  will not write

    Returns
    -------

    """
    # Add Survey
    print("Adding {:s} survey to DB".format(sname))
    kodiaq_grp = hdf.create_group(sname)
    # Load up
    meta = grab_meta()
    bmeta = meta_for_build()
    # Checks
    if sname != 'KODIAQ_DR1':
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
        raise ValueError("Bad matches in KODIAQ")
    meta_IDs = IDs[idx]

    # Loop me to bid the full survey catalog
    meta.add_column(Column(meta_IDs, name='IGM_ID'))

    # Build spectra (and parse for meta)
    nspec = len(meta)
    max_npix = 200000  # Just needs to be large enough
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
    Rlist = []
    wvminlist = []
    wvmaxlist = []
    gratinglist = []
    npixlist = []
    speclist = []
    # Loop
    #path = os.getenv('RAW_IGMSPEC')+'/KODIAQ_data_20150421/'
    path = os.getenv('RAW_IGMSPEC')+'/KODIAQ_data_20160618/'  # BZERO FIXED
    maxpix = 0
    for jj,row in enumerate(meta):
        # Generate full file
        full_file = path+row['qso']+'/'+row['pi_date']+'/'+row['spec_prefix']+'_f.fits'
        # Extract
        print("KODIAQ: Reading {:s}".format(full_file))
        hduf = fits.open(full_file)
        head = hduf[0].header
        spec = lsio.readspec(full_file)
        # Parse name
        fname = full_file.split('/')[-1]
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
        if head['XDISPERS'].strip() == 'UV':
            gratinglist.append('BLUE')
        else:
            gratinglist.append('RED')
        npixlist.append(npix)
        try:
            Rlist.append(iiu.set_resolution(head))
        except ValueError:
            pdb.set_trace()
        # Only way to set the dataset correctly
        if chk_meta_only:
            continue
        spec_set[jj] = data

    #
    print("Max pix = {:d}".format(maxpix))
    # Add columns
    meta.add_column(Column([2000.]*nspec, name='EPOCH'))
    meta.add_column(Column(speclist, name='SPEC_FILE'))
    meta.add_column(Column(npixlist, name='NPIX'))
    meta.add_column(Column(wvminlist, name='WV_MIN'))
    meta.add_column(Column(wvmaxlist, name='WV_MAX'))
    meta.add_column(Column(Rlist, name='R'))
    meta.add_column(Column(gratinglist, name='GRATING'))
    meta.add_column(Column(np.arange(nspec,dtype=int),name='SURVEY_ID'))

    # Add HDLLS meta to hdf5
    if iiu.chk_meta(meta):
        if chk_meta_only:
            pdb.set_trace()
        hdf[sname]['meta'] = meta
    else:
        raise ValueError("meta file failed")
    # References
    refs = [dict(url='http://adsabs.harvard.edu/abs/2015AJ....150..111O',
                 bib='kodiaq')
            ]
    jrefs = ltu.jsonify(refs)
    hdf[sname]['meta'].attrs['Refs'] = json.dumps(jrefs)
    #
    return


