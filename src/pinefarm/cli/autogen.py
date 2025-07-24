"""Autogenerate pinecards from NNPDF metadata."""

import click
import rich

from .. import configs
from ..external.nnlojet import generate_pinecard_from_nnpdf
from ._base import command


@command.command("autogen")
@click.argument("dataset", nargs=1)
@click.option(
    "--target",
    help="Target program. Currently only NNLOJET supported",
    default="NNLOJET",
)
@click.option(
    "--name", help="Name of the pinecard (NNLOJET_<name>), defaults to name=dataset"
)
@click.option(
    "--select-obs",
    help="Observables to select from the NNPDF available kinematics (max. 2D distributions)",
    type=str,
    nargs=2,
)
def runcards(dataset, target, select_obs=None, name=None):
    """Generate a runcard from an NNPDF dataset."""
    if name is None:
        name = dataset.upper()

    output = configs.configs["paths"]["runcards"] / f"{target}_{name}"

    if target.upper() == "NNLOJET":
        output_runcards = generate_pinecard_from_nnpdf(
            dataset, output_path=output, observables=select_obs
        )
    else:
        raise ValueError(f"Target {target} not recognized")

    rich.print("Pinecards written to: ")
    rich.print("    " + "\n".join(str(i) for i in output_runcards))
    rich.print("metadata.txt might be empty or incomplete, please modifiy it manually")
