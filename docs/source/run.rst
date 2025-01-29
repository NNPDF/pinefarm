Generating a PineAPPL grid
==========================

In the following section, we show to produced PineAPPL grids with `pinefarm`
and how to convert pre-existing interpolation grids in different formats
(ROOT, APPLgrid, fastNLO) into PineAPPL grids.

Producing a PineAPPL grid
-------------------------

To generate a |pineappl| grid run:

.. code-block:: sh

   pinefarm run <PINECARD> <THEORYCARD>

In order to get a list of available `pinecards <https://github.com/NNPDF/pinecards>`_ run:

.. code-block:: sh

   pinefarm list runcards

Recall to set the ``runcards`` parameter in :ref:`pinefarm.toml <install:configure paths>`

Analogously for theories:

.. code-block:: sh

   pinefarm list theories

Recall to set the ``theories`` parameter in :ref:`pinefarm.toml <install:configure paths>`


Converting pre-existing interpolation tables
--------------------------------------------

In some cases, when the interpolation tables are available in different format,
it is necessary to convert them into PineAPPL grids. In order for PineAPPL to
be able to convert those predictions, it needs to be compiled with the packages
from which those tables were produced. Often times, however, these packages are
hard to build because they rely on `Makefiles` that are inherently dependent on
the platform from which they were built.

An easy way to get these packages and build them with PineAPPL is to use
`nix-shell <https://nixos.wiki/wiki/Development_environment_with_nix-shell>`_.
`nix-shell` is a powerful tool from the `Nix <https://nixos.org/>`_ ecosystem
that provides a reproducible development environment without modifying the
system's global state.

The interactive nix-based shell and its package manager can be easily installed
using your OS' package manager by following the instructions on the installtion
`page <https://nixos.org/download/#download-nix>`_.

Then to use `nix-shell`, simply create a `shell.nix` file in the working directory
with the following contents:

.. code-block:: nix

   with import <nixpkgs> {}; {
     qpidEnv = stdenvNoCC.mkDerivation {
       name = "pineappl-with-all-features";
       buildInputs = [
           gcc10
           gfortran
           root
           lhapdf
           cargo
           cargo-c
           zlib
           fastnlo-toolkit
       ];
     };
   }

This will provide with all the necessary dependcies to build PineAPPL with all
the features (ROOT, fastNLO) except APPLgrid. APPLgrid therefore needs to be
compiled from source (see section below).

To invoke the shell, simpy run:

.. code-block:: sh

   nix-shell

One can check that everything has been set up correctly by checking (one of)
the following commands:

.. code-block:: sh

   gcc --version
   which root # Should point to nix/store/...
   fnlo-tk-config --help # Check fastNLO

We can now build APPLgrid by simply running the following commands:

.. code-block:: sh

   wget http://applgrid.hepforge.org/downloads/applgrid-1.6.27.tgz
   tar -zxvf applgrid-1.6.27.tgz
   ./configure --path=${prefix}
   make -j
   [sudo] make install
   export LD_LIBRARY_PATH=${prefix}/lib:$LD_LIBRARY_PATH

If everything went correctly, you should be able to run:

.. code-block:: sh

   applgrid-config --help

With all of the dependencies installed, we can now compile PineAPPL. Inside
the PineAPPL directory, run:

.. code-block:: sh

   APPL_IGRID_DIR=/path/to/applgrid-1.6.27/src cargo install --features=applgrid,fastnlo --path pineappl_cli

Once this is done, we can now for example convert a ROOT file into a PineAPPL
grid by running the following command:

.. code-block:: sh

   pineappl import <FILE_NAME>.root <PINEAPPL_NAME>.pineappl.lz4 NNPDF40_nnlo_as_01180
