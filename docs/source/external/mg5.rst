MadGraph5_aMC\@NLO
==================

|mg5| :cite:`Alwall:2014hca` :cite:`Frederix:2018nkq` is a general-purpose event generator
that is mainly used to compute observables in double hadronic environments such as the LHC.

Pinecard structure
------------------

- The ``output.txt`` file (compulsory). This file contains the instructions to
  generate the source code for the relevant process. For details, please see
  :cite:`Alwall:2014hca` and :cite:`Frederix:2018nkq`. The variable
  ``@OUTPUT@`` must be used to generate the directory containing the source
  files.

- The ``analysis.f`` file (compulsory). This Fortran file must fill the
  histograms from which the |hwu| files and
  the |pineappl| grids are generated. Note that a single histogram must not
  contain more than 100 bins, otherwise |mg5| will crash. However,
  big histograms can be split up into multiple histograms, for which the runner
  will merge the |pineappl| grids together.

- The ``*.patch`` file(s) (optional). These are one or more ``.patch`` files
  that are applied after |mg5| has generated the sources.

launch.txt (compulsory)
^^^^^^^^^^^^^^^^^^^^^^^
This file contains the instructions to
run the relevant process, including the relevant physical parameters and cuts.

Theory parameters
#################

To insert the actual values of the theory parameters coming from the theorycard
we provide a special syntax. You can use the names
``@GF``, ``@MH@``, ``@MT@``, ``@MW@``, ``@MZ@``, ``@WH@``, ``@WT@``, ``@WW@``,
and ``@WZ@``, which will be replaced with their numerical values upon generation.
The names are the same as chosen by ``mg5_aMC``, but written in
uppercase and surrounded with ``@``. For details about more parameters, please
see the ``Template/NLO/Cards/run_card.dat`` file in |mg5|.

Cuts
####

They are implemented in two steps:

1. cuts relevant *variables* are defined
2. cuts *code* is implemented

A list of available codes and variables can be obtained from the
`repository <https://github.com/NNPDF/pinefarm/tree/main/src/pinefarm/external/mg5>`_.

Patches
#######

For instance, to use a dynamical scale, a patch modifying ``setscales.f`` file
should be included in the directory. To create patches use the command ``diff
-Naurb original new > patch.patch``. The patches are applied in an unspecified
order, using ``patch -p1 ...``.

A list of available patches can be obtained from the
`repository <https://github.com/NNPDF/pinefarm/tree/main/src/pinefarm/external/mg5>`_.

Additional metadata
-------------------

- ``output.txt``: contains the generated ``output.txt`` script (after all
  substitutions have been done)
- ``launch.txt``: contains the generated ``launch.txt`` script (after all
  substitutions have been done)
- ``patch``: a list of patches' names, one per row (corresponding to those
  described in Patches)
- ``tau_min``: the minimum :math:`\tau` value set by the user
- ``user_cuts``: user defined cuts and cuts values, one per row in the format
  ``cut=value`` (cuts are those defined in Cuts)
- ``mg5amc_repo`` and ``mg5amc_revno``: The
  repository and revision number of the |mg5| version that was
  used to generate the grid.

.. note::

   It is guaranteed that the keys listed above are always present in grid's
   metadata (even if some of the corresponding values might be empty).

Output
------

- ``DATASET``: The directory created by ``mg5_aMC``. A few interesting files in
  this subdirectory are:

  - ``Events/-/MADatNLO.HwU``: |hwu|
  - ``Events/-/amcblast_obs_-.pineappl``: grids created by ``mg5_aMC``, not yet
    merged together

- ``output.txt``: Run card for the 'output' phase, with all variables substituted
  to their final values
- ``output.log``: Output of the external runner during the 'output' phase
- ``launch.txt``: Run card for the 'launch' phase, with all variables substituted
  to their final values
- ``launch.log``: Output of the external runner during the 'launch' phase
- ``results.log``: The numerical results of the run, comparing the results of the
  grid against the results from ``mg5_aMC``. The first column (PineAPPL) are the
  interpolated results, which should be similar to the Monte Carlo (MC) results
  in the second column. The third column gives the relative MC uncertainty
  (sigma). The next column gives the differences in terms of multiples of sigma.
  The final three columns give the per mille differences of the central, minimum, and
  maximum scale varied results. Ideally the first two columns are the same and
  the remaining columns are zero.
