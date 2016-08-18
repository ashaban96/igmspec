#!/usr/bin/env python

""" Loads (and can plot) a requested SDSS/BOSS spectrum
Default is by PLATE/FIBER
"""

import pdb

def parser(options=None):

    import argparse

    parser = argparse.ArgumentParser(description='sdss_igmspec script v0.1')
    parser.add_argument("plate", type=int, help="Plate")
    parser.add_argument("fiberid", type=int, help="FiberID")
    parser.add_argument("-s", "--survey", help="Name of Survey to use (BOSS_DR12 or SDSS_DR7)")
    parser.add_argument("--select", default=0, type=int, help="Index of spectrum to plot (when multiple exist)")
    parser.add_argument("-p", "--plot", default=False, action="store_true", help="Plot with lt_xspec")

    if options is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(options)
    return args


def main(args, unit_test=False, **kwargs):
    """ Run
    """
    import numpy as np
    from astropy.table import vstack
    from astropy.coordinates import SkyCoord
    from astropy import units as u
    from igmspec.igmspec import IgmSpec

    # init
    igmsp = IgmSpec(**kwargs)

    # Load meta table(s)
    if args.survey is None:
        #surveys = ['BOSS_DR12', 'SDSS_DR7']
        surveys = ['SDSS_DR7']
    else:
        surveys = [args.survey]
    for kk,survey in enumerate(surveys):
        itbl = igmsp.idb.hdf[survey]['meta'].value
        if kk > 0:
            mtbl = vstack([mtbl, itbl], join_type='inner')
        else:
            mtbl = itbl

    # Find plate/fiber
    imt = np.where((mtbl['PLATE'] == args.plate) & (mtbl['FIBERID'] == args.fiberid))[0]
    if len(imt) == 0:
        print("Plate and Fiber not found.  Try again")
        return
    else:
        mt = imt[0]
        scoord = SkyCoord(ra=mtbl['RA'][mt], dec=mtbl['DEC'][mt], unit='deg')

    # Grab
    print("Grabbing data for J{:s}{:s}".format(scoord.ra.to_string(unit=u.hour,sep='',pad=True),
                                              scoord.dec.to_string(sep='',pad=True,alwayssign=True)))
    all_spec, all_meta = igmsp.spec_from_coord(scoord, isurvey=surveys)

    # Outcome
    if len(all_meta) == 0:
        print("No source found, try another location or a larger tolerance.")
        return
    elif len(all_meta) == 1:  # One survey hit
        spec = all_spec[0]
        meta = all_spec[0]
    else:  # More than 1 survey
        idx = 0
        spec = all_spec[idx]
        meta = all_meta[idx]
        surveys = [meta.meta['survey'] for meta in all_meta]
        print("Source located in more than one survey")
        print("Using survey {:s}.  You can choose from this list {}".format(surveys[idx], surveys))

        #print("Choose another survey from this list (as you wish): {}".format(surveys))

    igmsp.idb.show_meta()

    # Load spectra
    spec.select = args.select
    if unit_test:
        return
    # Show  [may transition to xspec]
    if args.plot:
        spec.plot(xspec=True)
