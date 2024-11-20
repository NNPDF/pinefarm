####################################
Welcome to pinefarm's documentation!
####################################

`pinefarm` serves as common interface to several other external programs to compute |pineappl| grids :cite:`Carrazza:2020gss`.
It is part of the Pineline framework :cite:`Barontini:2023vmr`.

We currently support:

- |mg5i| |mg5| :cite:`Alwall:2014hca` :cite:`Frederix:2018nkq`
- |yadismi| |yadism| :cite:`yadism`
- Hawaiian Vrap :cite:`Barontini:2023vmr` (a modified version of Vrap :cite:`Anastasiou:2003ds`)
- PDF positivity observables :cite:`Candido:2020yat,Collins:2021vke,Candido:2023ujx`
- PDF integrability observables

.. |mg5i| image:: /external/mg5.png
   :align: middle
   :width: 150

.. |yadismi| image:: /external/yadism.png
   :align: middle
   :width: 150

To run `pinefarm` you need two specify to sets of inputs:

1. a theory runcard, as is used by `nnpdf <https://github.com/NNPDF/nnpdf>`_.
   The theory runcard defines the general parameters of the QCD framework, such as perturbative
   orders, coupling strength or heavy quark masses.
   A list of example theory runcards is also available
   `in the repository <https://github.com/NNPDF/pinefarm/tree/main/extras/theories>`_
2. a pinecard, as is described :doc:`here <pinecards>`.
   The pinecard describes the actual measurement that is performed, e.g. observable definitions,
   kinematic bins, or cuts. The pinecard will also determine which external program is executed.
   A list of already available observables can be inspected in the
   `pinecards repository <https://github.com/NNPDF/pinecards>`_.

Given those two things you can run

.. code-block:: sh

   pinefarm run <PINECARD> <THEORYCARD>

and the program will, if necessary, install the required external program and launch it's execution.


.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Usage

   install
   pinecards
   cli
   run
   output

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Interfaces

   external/index
   external/mg5
   external/yadism
   external/matrix
   external/vrap
   external/pos
   external/int

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Implementation

   API <modules/pinefarm/pinefarm>
   indices
   zzz-refs
