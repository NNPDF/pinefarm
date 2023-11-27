Overview
========

`pinefarm` itself is mostly physics agnostic, but the external programs
contain the actual physics.

If you want to add a new program take a look to the interface class
:class:`~pinefarm.external.interface.External`
from which you should derive your new interface.
