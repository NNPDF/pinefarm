External runners
================

The ``pinefarm`` is mainly a uniform interface to
several other generators which actually produce PineAPPL grids.

If you want to add a new program take a look to the interface class
:class:`~pinefarm.external.interface.External`
from which you should derive your new interface.
