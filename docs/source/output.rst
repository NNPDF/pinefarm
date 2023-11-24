What is all the output?
=======================

After having run ``pinefarm run <PINECARD> <THEORYCARD>`` (see :doc:`cli`), the script
prints a table, which is useful to quickly validate the native output and the
interpolation error of |pineappl|. The last line shows the directory where all
results are stored, which has the form ``PINECARD-DATE``, where ``PINECARD`` is
the value given to the run script and ``DATE`` is a numerical date when the
generation was started. The date is added so runs for the same dataset do not
overwrite each other's output.

The most important file in the output directory is

    ``PINECARD-DATE/PINECARD.pineappl.lz4``

which is the final |pineappl| grid.

The remaining contents of this directory are useful for testing and debugging:

- ``results.log``: The numerical results of the run, comparing the results of the
  grid against the native results from the runner.


Metadata
--------

The resulting |pineappl| grid will contain the metadata written in the
``metadata.txt`` file.

In addition, ``pinefarm`` will automatically add the following metadata:

- ``initial_state_{1,2}``: The hadronic initial states of the grid, given as
  |pid|, typically ``2212`` for protons, ``-2212`` for anti-protons, and so on.
- ``lumi_id_types``: The meaning of the luminosities IDs in the definition of
  the luminosity function of a |pineappl| grid. This is set to ``pdg_mc_ids`` to
  signal they are |pid| (with a possible exception of the gluon, for which
  ``0`` may be used).
- ``pineappl``: The |pineappl| version that was used to generate the grid.
- ``pinefarm``: The ``pinefarm`` version that was used to generate the grid.
- ``pinecard``: `Base64 <https://en.wikipedia.org/wiki/Base64>`_ encoded ``.tar.gz`` version
  of the generating pinecard. To re-extract it on a UNIX system run
  ``pineappl read --get pinecard PINECARD.pineappl.lz4 | base64 -d > PINECARD.tar.gz`` where ``PINECARD``
  is to be replaced with the actual file name.
- ``results``: The comparison of the raw generator results against a convolution of the
  |pineappl| grid with the selected PDF. This is the same table
  printed at the end by ``pinefarm run``, and is used to verify the contents of each
  grid.
- ``results_pdf``: PDF used for the comparison table

Runner dependent output
-----------------------

Part of the output is specific to the selected runner, and described in the
corresponding :doc:`section <external/index>`.
