"""External interfaces module.

All imports of external interfaces are 'hidden'
under the function ``decide_external_tool`` to avoid
unnecessary installations of external codes.
"""

from ..configs import configs


def decide_external_tool(dsname):
    """Decide the external tool to be used.

    This function uses completely arbitrary reasons to select a tool.

    Parameters
    ----------
        dsname: str
            name of the pinecard

    Returns
    -------
        external_interface: External
            external interface to be used
        color:
            color code of the interface
    """
    # The decisions are usually based on the existence of a `.yaml` file with a specific name
    # or a prefix in the pinecard

    # DIS with yadism
    if (configs.configs["paths"]["runcards"] / dsname / "observable.yaml").exists():
        from . import yad

        return yad.Yadism, "red"

    if (configs.configs["paths"]["runcards"] / dsname / "vrap.yaml").exists():
        from . import vrap

        return vrap.Vrap, "green"

    if (configs.configs["paths"]["runcards"] / dsname / "positivity.yaml").exists():
        from . import positivity

        return positivity.Positivity, "yellow"

    if (configs.configs["paths"]["runcards"] / dsname / "integrability.yaml").exists():
        from . import integrability

        return integrability.Integrability, "brown"

    # Defaults to Madgraph
    from . import mg5

    return mg5.Mg5, "blue"
