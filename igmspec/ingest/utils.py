""" Module to for ingest utilities
"""
from __future__ import print_function, absolute_import, division, unicode_literals

import numpy as np
import warnings
import pdb

def chk_meta(meta):
    """ Vettes a meta Table prior to its being ingested into the hdf

    Parameters
    ----------
    meta

    Returns
    -------
    chk : bool

    """
    from igmspec.defs import instruments
    from astropy.time import Time
    from astropy.table import Column
    # Init
    inst_dict = instruments()

    chk = True
    # Required columns
    req_clms = ['IGM_ID', 'RA', 'DEC', 'EPOCH', 'zem', 'R', 'WV_MIN',
                'WV_MAX', 'DATE-OBS', 'SURVEY_ID', 'NPIX', 'SPEC_FILE',
                'INSTR', 'GRATING', 'TELESCOPE']
    meta_keys = meta.keys()
    for clm in req_clms:
        if clm not in meta_keys:
            chk = False
            print("Missing column {:s} in meta".format(clm))
    # Check date formatting
    try:
        tval = Time(list(meta['DATE-OBS'].data), format='iso')
    except:
        print("Bad DATE-OBS formatting")
        chk = False
    # Check instrument
    meta_instr = meta['INSTR'].data
    db_instr = np.array(inst_dict.keys())
    if not np.all(np.in1d(meta_instr, db_instr)):
        print("Bad instrument in meta data")
        chk = False
    # Check for unicode
    for key in meta_keys:
        if 'unicode' in meta[key].dtype.name:
            warnings.warn("unicode in column {:s}.  Will convert to str for hdf5".format(key))
            tmp = Column(meta[key].data.astype(str), name=key)
            meta.remove_column(key)
            meta[key] = tmp
    # Return
    return chk


def set_resolution(head, instr=None):
    """ Sets resolution based on the instrument and header

    Parameters
    ----------
    head : FITS header
    instr : str, optional
      If not provided, attempt to grab from header

    Returns
    -------

    """
    from igmspec import defs
    # Dicts
    Rdicts = defs.get_res_dicts()
    # Grab instrument
    if instr is None:
        if 'CURRINST' in head.keys():  # ESI
            instr = head['CURRINST'].strip()
        elif 'INSTRUME' in head.keys():
            if 'HIRES' in head['INSTRUME']:
                instr = 'HIRES'
            elif 'MagE' in head['INSTRUME']:
                instr = 'MagE'
        else:
            pass
        if instr is None:
            raise ValueError("NEED MORE INFO FOR INSTR")

    # Grab resolution
    if instr == 'ESI':
        try:
            return Rdicts[instr][head['SLMSKNAM']]
        except KeyError:
            pdb.set_trace()
    elif instr == 'HIRES':
        try:
            return Rdicts[instr][head['DECKNAME'].strip()]
        except KeyError:
            print("Need to add {:s}".format(head['DECKNAME']))
            pdb.set_trace()
    elif instr == 'MagE':
        try:
            return Rdicts[instr][head['SLITNAME'].strip()]
        except KeyError:
            print("Need to add {:s}".format(head['SLITNAME']))
            pdb.set_trace()
    else:
        raise IOError("Not read for this instrument")
