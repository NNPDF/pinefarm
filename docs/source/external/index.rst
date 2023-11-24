Overview
========

``pinefarm`` is mainly a uniform interface to
several other generators which actually produce |pineappl| grids.
`pinefarm` itself is mostly agnostic to physics.

If you want to add a new program take a look to the interface class
:class:`~pinefarm.external.interface.External`
from which you should derive your new interface.

We currently support:

- |mg5i| |mg5| - see :doc:`here <mg5>`
- |yadismi| |yadism| - see :doc:`here <yadism>`
