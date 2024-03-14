"""Autogenerate pinecards from NNPDF metadata"""

import click

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
def runcards(dataset, target):
    """Generate a runcard from an NNPDF dataset"""
    output = configs.configs["paths"]["runcards"] / f"{target}_{dataset.upper()}"

    if target == "NNLOJET":
        output_runcards = generate_pinecard_from_nnpdf(dataset, output_path=output)

    print("Runcards written to: ")
    print("\n".join(str(i) for i in output_runcards))
    print("metadata.txt might be empty or incomplete, please modifiy it manually")
