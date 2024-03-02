"""Autogenerate pinecards from NNPDF metadata"""

import click

from .. import configs
from ..external.nnlojet import generate_pinecard_from_nnpdf
from ._base import command

try:
    from validphys.datafiles import path_commondata
    from validphys.theorydbutils import make_query
    from yaml import safe_dump
except ModuleNotFoundError:
    make_query = None


@command.command("autogen")
@click.argument("dataset", nargs=1)
@click.option(
    "--target",
    help="Target program. Currently only NNLOJET supported",
    default="NNLOJET",
)
@click.option("--theory", help="Theory ID to autogenerate with NNPDF numeration")
def runcards(dataset, target, theory):
    """Generate a runcard from an NNPDF dataset"""
    output = configs.configs["paths"]["runcards"] / f"{target}_{dataset.upper()}"

    if target == "NNLOJET":
        output_runcards = generate_pinecard_from_nnpdf(dataset, output_path=output)

    print("Runcards written to: ")
    print("\n".join(str(i) for i in output_runcards))
    print("metadata.txt might be empty or incomplete, please modifiy it manually")

    if theory is not None:
        # TODO: the sqlite db will be changed before this is merged to pinefarm
        # so don't rely on this
        if make_query is None:
            raise ModuleNotFoundError("Cannot autogenerate theories without NNPDF")

        theories_path = configs.configs["paths"]["theories"] / f"{theory}.yaml"
        if theories_path.exists():
            print(
                f"Theory {theory} already exists at {theories_path}. Not overwritting"
            )
            return

        theories_path.parent.mkdir(exist_ok=True)

        query = f"SELECT * FROM TheoryIndex WHERE ID={theory}"
        res = make_query(query, path_commondata.parent / "theory.db")
        val = res.fetchone()
        theory_info_dict = {k[0]: v for k, v in zip(res.description, val)}
        safe_dump(theory_info_dict, theories_path.open("w", encoding="utf-8"))
        print(f"Theory {theory} written to {theories_path}")
