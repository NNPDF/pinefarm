
Installation
============

Eventually create a new virtual environment and then just run

.. code-block:: sh

    pip install pinefarm


Non Python dependencies
-----------------------

Even if the installation management tries to reduce as
much as possible the amount of dependencies, still a few ingredients have to be
available on the system.

To install `MadGraph5_aMC@NLO <http://madgraph.phys.ucl.ac.be/>`_ and its dependencies:

- ``gfortran``
- ``wget``

and that will also require a development installation of ``pineappl`` which requires:

- ``pkg-config``
- ``openssl`` (e.g. on Debian available in the ``libssl-dev`` package)



Configure paths
---------------

Pinefarm is acting as an interface to other external programs, which it will try to install
and manage on its own (the additional dependencies above are the exception).
However, in some situtations it might be advantages to control path and executables by hand:
this can be configured via the ``pinefarm.toml`` file.

Please take a look to `the template configuration <https://github.com/NNPDF/pinefarm/blob/main/pinefarm.toml>`_
provided in the repository for a list of available options.

``pinefarm`` can still run without the configuration file present, by assuming some default values.


Install in development mode
---------------------------

For development you need in addition the following tools:

- `poetry`, follow `installation instructions <https://python-poetry.org/docs/#installation>`_
- `poetry-dynamic-versioning`, used to manage the version (see
  `repo <https://github.com/mtkennerly/poetry-dynamic-versioning>`_)
- `pre-commit`, to run maintenance hooks before commits (see
  `instructions <https://pre-commit.com/#install>`_)

Then you can run

.. code-block:: sh

    poetry install


To access the CLI you can run

.. code-block:: sh

    poetry run pinefarm <args>
