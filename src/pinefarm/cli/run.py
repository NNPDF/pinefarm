"""Compute a grid and compare using a given PDF."""

import logging
import pathlib
import sys
import time

import click
import rich
import yaml

from .. import configs, info, install, log, table, tools
from ..external import mg5
from ._base import command

logger = logging.getLogger(__name__)


@command.command("run")
@click.argument("pinecard")
@click.argument("theory-path", type=click.Path(exists=True))
@click.option(
    "--pdf",
    help="PDF to compare the original results to the grid",
    default="NNPDF40MC_nnlo_as_01180_qed",
)
@click.option("--dry", is_flag=True, help="Don't execute the underlying code")
@click.option(
    "--finalize",
    type=click.Path(exists=True),
    help="Run the postprocess step given a runfolder",
)
def subcommand(pinecard, theory_path, pdf, dry, finalize=None):
    """Compute the grids as defined in the given pinecard.

    Given a PINECARD and a THEORY-PATH, pinefarm will execute the
    appropiate external program to generate the grids.

    The given PDF will be used to compare the original results (from the generator) with PineAPPL interpolation - this checks any interpolation issues.
    Setting the DRY flag prevents the generator from actually running.

    Note: not all external programs can be automatically run by pinefarm,
    in those cases only the relevant run files will be generated.
    Pinefarm provides a ``--finalize`` flag to wrap up the grid and add relevant metadata.

    \f

    Parameters
    ----------
        pinecard: str
            pinecard name
        theory_path: pathlib.Path
            path to a theory card
        pdf: str
            pdf name
        dry: bool
            run only the preparation step
        finalize: str
            path to the runfolder in which to run the post processing step
    """
    # Check whether pinecard is a path. If it is, override the configuration.
    if (pinpath := pathlib.Path(pinecard)).exists():
        # If this pinecard is not in the runcards folder, warn the user but let it continue
        if pinpath.parent.absolute() != (
            rcards := configs.configs["paths"]["runcards"]
        ):
            logger.warning(
                f"The pinecard ({pinecard}) is not in the runcards ({rcards}) folder, overriding config."
            )
            configs.configs["paths"]["runcards"] = pinpath.parent
        pinecard = pinpath
    # Otherwise, use the configuration to fill the path
    else:
        pinecard = configs.configs["paths"]["runcards"] / pinecard

    # Check for existence
    if not pinecard.exists():
        raise FileNotFoundError(f"The pinecard {pinecard} cannot be found")

    if finalize is not None:
        finalize = pathlib.Path(finalize)

    # read theory card from file
    with open(theory_path) as f:
        theory_card = yaml.safe_load(f)
        # Fix (possible) problems with CKM matrix loading
        if isinstance(theory_card.get("CKM"), str):
            theory_card["CKM"] = [float(i) for i in theory_card["CKM"].split()]

    # _in principle_ the pinecard is just the name, but a path should also be accepted
    dataset = pinecard.name

    # Check for old, unsupported behaviour
    if "-" in dataset:
        # NB: originally, instead of a finalize flag, pinefarm would decide whether to run
        # in "postprocessing" mode according to whether the input was a pinecard or a runfolder
        # This behaviour was not documented and now errors out
        dataset_raw, timestamp = dataset.rsplit("-", 1)
        try:
            # Check whether the timestamp is really an integer
            _ = int(timestamp)
            pinecard = dataset_raw
            raise ValueError(
                f"""Using a runfolder as a pinecard. This behaviour is no longer supported.
    Please, run instead using the --finalize flag.

    ~$ pinefarm run {pinecard} --finalize {dataset}
"""
            )
        except ValueError:
            timestamp = None

    rich.print(dataset)

    try:
        datainfo = info.label(dataset)
    except UnboundLocalError as e:
        raise UnboundLocalError(f"Runcard {dataset} could not be found") from e

    rich.print(f"Computing [{datainfo.color}]{dataset}[/]...")

    runner = datainfo.external(dataset, theory_card, pdf, output_folder=finalize)
    install_reqs(runner, pdf)

    # Run the preparation step of the runner (if any)
    if finalize is None:
        runner_stop = runner.preparation()
        if dry or runner_stop:
            rich.print(
                f"""Running in dry mode, exiting now.
    The preparation step can be found in:
        {runner.dest}"""
            )
            sys.exit(0)

        ###### <this part will eventually go to -prepare->

    run_dataset(runner)


def install_reqs(runner, pdf):
    """Install requirements.

    Parameters
    ----------
    runner : interface.External
        runner instance
    pdf : str
        pdf name

    """
    t0 = time.perf_counter()

    install.init_prefix()
    install.update_environ()
    runner.install()

    # install chosen PDF set
    install.lhapdf_conf(pdf)

    # lhapdf_management determine paths at import time, so it is important to
    # late import it, in particular after environ has been updated by `install.lhlhapdf_conf`
    import lhapdf_management  # pylint: disable=import-error,import-outside-toplevel

    try:
        lhapdf_management.pdf_update()
    # survive even if it's not possible to write 'pdfsets.index'
    except PermissionError:
        pass
    lhapdf_management.pdf_install(pdf)

    tools.print_time(t0, "Installation")


def run_dataset(runner):
    """Execute runner and apply common post process.

    Parameters
    ----------
    runner : interface.External
        runner instance

    """
    t0 = time.perf_counter()

    tools.print_time(t0, "Grid calculation")

    with log.Tee(runner.dest / "errors.log", stdout=False, stderr=True):
        # if output folder specified, do not rerun
        if runner.timestamp is None:
            runner.run()

            # collect results in the output pineappl grid
            runner.generate_pineappl()

            table.print_table(
                table.convolute_grid(
                    runner.grid, runner.pdf, integrated=isinstance(runner, mg5.Mg5)
                ),
                runner.results(),
                runner.dest,
            )

            # TODO: annotate_version should be a post-processing step
            # however at the moment only works in 1-grid cases
            runner.annotate_versions()

        runner.postprocess()

    print(f"Output stored in {runner.dest}")
