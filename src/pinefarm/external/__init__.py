"""External interfaces module.

All imports of external interfaces are 'hidden'
under the function ``decide_external_tool`` to avoid an
eager import and thus unnecessary installations of external codes.
"""

from ..configs import configs
from .interface import External


def decide_external_tool(dsname: str) -> tuple[External, str]:
    """Decide the external tool to be used.

    The decisions are based on the existence of a `.yaml` file with a specific name.

    Parameters
    ----------
    dsname:
        name of the pinecard

    Returns
    -------
    external_interface:
        external interface to be used
    color:
        color code of the interface
    """
    if (configs["paths"]["runcards"] / dsname / "observable.yaml").exists():
        from . import yad  # pylint: disable=import-outside-toplevel

        return yad.Yadism, "red"

    if (configs["paths"]["runcards"] / dsname / "vrap.yaml").exists():
        from . import vrap  # pylint: disable=import-outside-toplevel

        return vrap.Vrap, "green"

    if (configs["paths"]["runcards"] / dsname / "positivity.yaml").exists():
        from . import positivity  # pylint: disable=import-outside-toplevel

        return positivity.Positivity, "yellow"

    if (configs["paths"]["runcards"] / dsname / "integrability.yaml").exists():
        from . import integrability  # pylint: disable=import-outside-toplevel

        return integrability.Integrability, "brown"

    # Defaults to Madgraph
    from . import mg5  # pylint: disable=import-outside-toplevel

    return mg5.Mg5, "blue"
