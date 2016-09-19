""" Module for key definitions in the IGMspec database
"""
from __future__ import print_function, absolute_import, division, unicode_literals

import numpy as np
import pdb

from collections import OrderedDict
from astropy import units as u

def instruments():
    """ Dict of allowed instruments (and definitions)

    Includes allowed gratings

    Returns
    -------
    inst_dict

    """
    inst_dict = {
        # Spectrograph for SDSS-III (BOSS) survey ; https://www.sdss3.org/instruments/boss_spectrograph.php
        'BOSS': dict(gratings=['BLUE', 'RED', 'BOTH']),
        # Spectrograph for SDSS-I/II survey; http://classic.sdss.org/dr7/instruments/spectrographs/index.html
        'SDSS': dict(gratings=['BLUE', 'RED', 'BOTH']),
        # Keck/HIRES spectrometer -- BLUE/RED refer to the cross-disperser
        'HIRES': dict(gratings=['UV', 'BLUE', 'RED', 'BOTH']),
        # Keck/ESI spectrometer -- ECH
        'ESI': dict(gratings=['ECH']),
        # Keck/LRIS spectrometer
        'LRISb': dict(gratings=['ECH']),
        'LRISr': dict(gratings=['ECH']),
        # Keck/NIRSPEC spectrometer
        'NIRSPEC': dict(gratings=['Low-Res']),
        # Keck/MOSFIRE spectrometer
        'MOSFIRE': dict(gratings=['H']),
        # Magellan MIKE spectrometer
        'MIKE': dict(gratings=['BOTH']),   # HD-LLS spliced blue and red
        'MIKE-Blue': dict(gratings=['BLUE']),
        'MIKE-Red': dict(gratings=['RED']),
        'MIKEb': dict(gratings=['BLUE']),
        'MIKEr': dict(gratings=['RED']),
        # Magellan MagE spectrometer
        'MagE': dict(gratings=['N/A']),
        # MMT BCS
        'MMT': dict(gratings=['??']),
        'mmtbluechan': dict(gratings=['500GPM']),
        # LBT/MODS
        'MODS1B': dict(gratings=['G400L']),
        'MODS1R': dict(gratings=['G670L']),
        # Gemini
        'GMOS-S': dict(gratings=['R400', 'B600']),
        'GMOS-N': dict(gratings=['R400', 'B600']),
        'GNIRS': dict(gratings=['ECH']),
        'NIRI': dict(gratings=['Hgrism_G5203','Kgrism_G5204']),
        # UKST
        '2dF': dict(gratings=['300B']),
        # HST
        'ACS': dict(gratings=['PR200L']),
        'WFC3': dict(gratings=['G280']),
        'COS': dict(gratings=['G130M', 'G160M', 'G130M/G160M']),
        # VLT
        'XSHOOTER': dict(gratings=['UVB,VIS,NIR,ALL']),
        'ISAAC': dict(gratings=['SW_MRes']),
        # Palomar
        'TSpec': dict(gratings=['ECH']),
    }
    return inst_dict

def list_of_stypes():
    """ List of source types
    Returns
    -------
    stypes : list

    """
    stypes = [
        str('QSO'),        # Quasars
        str('GRB'),        # Gamma ray burst
    ]
    return stypes

def z_priority():
    """ List of redshift priorities for setting the DB redshift
    See also myers.zbest_myers

    Returns
    -------
    zpri : list

    """
    zpri = [
        str('GGG'),        # GGG redshifts
        str('SDSS-HW'),    # SDSS redshifts with Hewitt&Wild
        str('BOSS_PCA'),   # PCA analysis by Paris et al. 2015 on BOSS spectra
        str('XQ-100'),     # XQ-100 redshifts
        str('BOSS_PIPE'),  # BOSS Pipeline redshifts
        str('2QZ'),        #
        str('2SLAQ'),      #
        str('AUS'),
        str('AGES'),
        str('COSMOS'),
        str('FAN'),
        str('MMT'),
        str('PAPOVICH'),
        str('GLIKMAN'),
        str('MADDOX'),
        str('LAMOST'),
        str('MCGREER'),
        str('VCV'),
        str('ALLBOSS'),
        str('UNKN'),       # Unknown
    ]
    return zpri

def get_cat_dict():
    """ Definitions for the catalog
    Returns
    -------

    """
    cdict = dict(match_toler=2*u.arcsec)
    return cdict


def get_db_table_format():
    """ Returns DB Table format

    Returns
    -------
    idict : dict
      Describes the table columns
    """
        # Defs
    zpri = z_priority()
    lenz = [len(zpi) for zpi in zpri]
    dummyf = str('#')*np.max(np.array(lenz))  # For the Table
    stypes = list_of_stypes()
    lens = [len(stype) for stype in stypes]
    dummys = str('#')*np.max(np.array(lens))  # For the Table

    # Dict for Table
    idict = dict(RA=0., DEC=0., IGM_ID=0, zem=0., sig_zem=0.,
                 flag_zem=dummyf, flag_survey=0, STYPE=dummys)
    # Return
    return idict


def get_survey_dict():
    """ Return the survey dict
    Returns
    -------

    """
    survey_dict = OrderedDict()
    survey_dict['BOSS_DR12'] = 1
    survey_dict['SDSS_DR7'] = 2
    survey_dict['KODIAQ_DR1'] = 4   # O'Meara et al. 2016
    survey_dict['HD-LLS_DR1'] = 8   # Prochaska et al. 2015
    survey_dict['GGG'] = 16         # Worseck et al. 201X
    survey_dict['HST_z2'] = 2**5    # O'Meara et al. 2011
    survey_dict['XQ-100'] = 2**6    # Lopez et al. 2016
    survey_dict['HDLA100'] = 2**7   # Neeleman et al. 2013
    survey_dict['2QZ'] = 2**8       # Croom et al.
    survey_dict['ESI_DLA'] = 2**9   # Rafelski et al. 2012, 2014
    survey_dict['COS-Halos'] = 2**10 # Tumlinson et al. 2013
    survey_dict['HSTQSO'] = 2**12 # Ribaudo et al. 2011; Neeleman et al. 2016
    #
    return survey_dict


def survey_flag(survey, iflag=None):
    """ Defines bitwise survey flag for IGMspec
    Parameters
    ----------
    survey : str
      Name of the survey
    iflag : int, optional
    Returns
    -------
    flag_val : int

    """
    survey_dict = get_survey_dict()
    #
    return survey_dict[survey]


def get_res_dicts():
    """ Resolution dicts

    Returns
    -------
    Rdicts : dict
      dict of R dicts

    """
    ESI_Rdict = {'0.50_arcsec': 4545./0.5, '0.75_arcsec': 4545./0.75,
                 '1.00_arcsec': 4545./1., 'Unknown': 4545./1.}
    HIRES1 = 36000.*1.148  # https://koa.ipac.caltech.edu/UserGuide/deckname_detail.html
    HIRES_Rdict = {'C1': HIRES1/0.861,
                   'C2': HIRES1/0.861,
                   'C5': HIRES1/1.148,
                   'D1': HIRES1/1.148,
                   'B2': HIRES1/0.574,
                   'B5': HIRES1/0.861,
                   'E3': HIRES1/0.4,
                   }
    LRISb_Rdict = {'400/3400': 500.,      # Assumes 1" slit
                   '600/4000': 1000.,
                   '1200/3400': 2180.,
                   }
    LRISr_Rdict = {'600/7500': 1595.,     # Assumes 1" slit
                   '400/8500': 1232.,
                   '1200/7500': 2*1595.,
                   }
    MOSFIRE_Rdict = {'H': 3660,  # Assumes 0.7" slit
                     }
    MMT_Rdict = {'500GPM': 1430, '800GPM': 1730.}          # Assumes 1" slit
    MODS_Rdict = {'G400L': 1850, 'G670L': 2300.}          # Assumes 0.6" slit
    GMOS_Rdict = {'B600+_G5307': 844.,    # Assumes 1" slit
                  'B600+_G5323': 844.,
                  'B1200+_G5301': 1872.,
                  }
    GNIRS_Rdict = {'32/mm_G5506': 1700.,    # Assumes 0.3" slit
                   '32/mmSB_G5533': 1700.,
                  }
    NIRI_Rdict = {'Hgrism_G5203': 940.,    # Assumes 4 pixels
                  'Kgrism_G5204': 780.,    # Assumes 4 pixels
                  }
    #
    Rdicts = dict(ESI=ESI_Rdict, HIRES=HIRES_Rdict,
                  GMOS=GMOS_Rdict, GNIRS=GNIRS_Rdict, LRISb=LRISb_Rdict,
                  LRISr=LRISr_Rdict, mmt=MMT_Rdict, MODS1B=MODS_Rdict,
                  MODS1R=MODS_Rdict, NIRI=NIRI_Rdict, MOSFIRE=MOSFIRE_Rdict,
                  )
    Rdicts['MIKE-Blue'] = 28000. # 1" slit
    Rdicts['MIKE-Red'] = 22000. # 1" slit
    #
    return Rdicts


def slit_width(slitname, req_long=True):
    """ Slit width

    Parameters
    ----------
    slitname : str
    req_long : bool, optional
      Require long in slit name.  If not present return 1.0

    Returns
    -------
    sdict : dict
      Translates slit mask name to slit with in arcsec or pixels

    """
    sdict = {'long_1.0': 1.0,
             'long_1.5': 1.5,
             '1.0x180': 1.0,  # MMT
             'LS5x60x0.6': 0.6,  # MODS
             '0.30 arcsec': 0.3,  # GNIRS
             'f6-4pix_G5212': 4., # NIRI
             '42x0.570': 0.57, # NIRSPEC
             'LONGSLIT-46x0.7': 0.7, # MOSFIRE
             }
    #
    try:
        swidth = sdict[slitname]
    except KeyError:
        try:
            swidth = float(slitname)
        except ValueError:
            if ('long' not in slitname) & req_long:
                    swidth = 1.
            else:
                pdb.set_trace()
    #
    return swidth


def get_req_clms():
    """
    Returns
    -------
    req_clms : list
      List of required columns for meta data
    """
    req_clms = ['RA', 'DEC', 'EPOCH', 'zem', 'R', 'WV_MIN',
            'WV_MAX', 'DATE-OBS', 'SURVEY_ID', 'NPIX', 'SPEC_FILE',
            'INSTR', 'GRATING', 'TELESCOPE', 'IGM_ID']
    return req_clms
