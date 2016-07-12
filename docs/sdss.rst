.. highlight:: rest

************
SDSS Dataset
************

This document describes the SDSS dataset.

Sources
=======

The igmspec database is intended to include all of the
quasar spectra in the SDSS DR7 data release.  The current
version is a home-grown set of quasars compiled by JXP.

Meta Data
=========

Here are the additional keys included in the meta data:

============  ======== =========================================
Key           Type     Description
============  ======== =========================================
Z_CONF        float    Confidence in the redshift measurement
Z_WARN        int      Warning flag
PLATE         int      Plate number
MJD           int      MJD of observation
FIBERID       int      Fiber ID
FLG_TARG      int      Targeting flag
PSF_X         float    PSF magnitude for X=[U,G,R,I,Z]
PSF_SX        float    Error in PSF magnitude for X=[U,G,R,I,Z]
============  ======== =========================================

Spectra
=======

Spectra straight from the SDSS database.
Future igmspec releases will include continua.
