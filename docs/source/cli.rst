``pinefarm`` command line interface
===================================

You can get the full update help of the command line interface (CLI) with:

.. code-block:: sh

   pinefarm --help

Below we present a brief recap of the subcommands and their goal.

``install``
-----------

Installs various programs, used to run pinecards.

``run``
-------

It is the main command provided, and it runs the specified pinecard in the
context of the selected theory.

The output will be stored in a directory in the current path, with the name
``<RUNCARD>-<YYYYMMDDhhmmss>``, where:

- the first part is the name of the selected pinecard (that is also the name of
  the folder in which all the files are stored)
- the second part is the timestamp of the moment in which the command is issued

``update``
---------

Update the metadata of the specified grid, with the content of the
``metadata.txt`` file in the current version of the pinecard.

``merge``
---------

Merge the specified grids' content into a new grid.
