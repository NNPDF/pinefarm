Yadism
======

|yadism| :cite:`yadism` is a coefficient functions library that is used to compute
fully inclusive structure functions and cross sections in deep-inelastic scattering (DIS) experiments.

Pinecard structure
------------------

- The ``observable.yaml`` file (compulsory). This file contains the description
  of the observable requested (kind and kinematics), together with further
  parameters specifying the process, and the details of the |yadism| calculation

Additional metadata
-------------------

- ``yadism_version``: The |yadism| version used to generate the grids

Output
------

- ``<PINECARD>.yaml``: is the other |yadism| output format, fully human readable
  (but a bit verbose)
