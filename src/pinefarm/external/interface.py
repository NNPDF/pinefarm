"""Abstract interface."""

import abc
import base64
import os
import pathlib
import shutil
import subprocess
import tempfile

import pineappl

from .. import __version__, configs, install, tools


class External(abc.ABC):
    """Interface class for external providers.

    Parameters
    ----------
    name : str
        dataset name
    theory : dict
        theory dictionary
    pdf : str
        PDF name
    timestamp : str
        timestamp of already generated output folder
    output_folder : pathlib.Path
        path of the already generated output folder

    """

    kind = None

    def __init__(
        self, name, theory, pdf, timestamp=None, runcards_path=None, output_folder=None
    ):
        self.name = name
        self.theory = theory
        self.pdf = pdf
        self.timestamp = timestamp
        if runcards_path is None:
            self._runcards_path = configs.configs["paths"]["runcards"]
        else:
            self._runcards_path = pathlib.Path(runcards_path)

        if timestamp is None and output_folder is None:
            self.dest = tools.create_output_folder(self.name, self.theory["ID"])
        elif timestamp is None:
            # If an output_folder is present, it takes precedence with respect to the timestamp
            self.dest = output_folder
            self.timestamp = output_folder.as_posix().split("-")[-1]
            if (
                not self.grid.exists()
                and self.grid.with_suffix(".pineappl.lz4").exists()
            ):
                tools.decompress(self.grid.with_suffix(".pineappl.lz4"))
        else:
            self.dest = configs.configs["paths"]["results"] / (
                str(theory["ID"]) + "-" + self.name + "-" + self.timestamp
            )
            if not self.grid.exists():
                tools.decompress(self.grid.with_suffix(".pineappl.lz4"))

    @property
    def source(self):
        """Runcard base directory."""
        return self._runcards_path / self.name

    @property
    def grid(self):
        """Target PineAPPL grid name."""
        return self.dest / f"{self.name}.pineappl"

    @property
    def gridtmp(self):
        """Intermediate PineAPPL grid name."""
        return self.dest / f"{self.name}.pineappl.tmp"

    def update_with_tmp(self, output_grid=None):
        """Move intermediate grid to final position."""
        if output_grid is None:
            output_grid = self.grid
        shutil.move(str(self.gridtmp), str(output_grid))

    @staticmethod
    def install():
        """Install all needed programs."""
        # Everybody needs LHAPDF unless explicitly skipped
        _ = install.lhapdf()

    def preparation(self):
        """Run the preparation method of the runner."""
        return False

    @abc.abstractmethod
    def run(self):
        """Execute the program."""

    @abc.abstractmethod
    def generate_pineappl(self):
        """Generate PineAPPL grid and extract output.

        Returns
        -------
        str
            output of ``pineappl convolute`` on the generate grid and selected
            :attr:`pdf`

        """

    @abc.abstractmethod
    def results(self):
        """Results as computed by the program.

        Returns
        -------
        pandas.DataFrame
            standardized dataframe with results (containing ``result``,
            ``error``, ``sv_min``, and ``sv_max`` columns)

        """

    @abc.abstractmethod
    def collect_versions(self) -> dict:
        """Collect necessary version informations.

        Returns
        -------
        dict
            program - version mapping related to programs specific to a single
            runner (common ones are already abstracted)

        """

    def load_pinecard(self) -> str:
        """Load directory as b64encoded .tar.gz file."""
        # shutils wants to create a true file, so we go through a temp dir
        with tempfile.TemporaryDirectory() as tmpdirname:
            p = pathlib.Path(tmpdirname) / "pinecard"
            shutil.make_archive(p, format="gztar", root_dir=self.source)
            with open(p.with_suffix(".tar.gz"), "rb") as fd:
                return base64.b64encode(fd.read()).decode("ascii")

    def annotate_versions(self):
        """Add version informations as meta data."""
        results_log = self.dest / "results.log"

        versions = self.collect_versions()
        # the pinefarm version will also pin pineappl_py version and all the
        # other python dependencies versions
        versions["pinefarm"] = __version__
        versions["pinecard"] = self.load_pinecard()
        versions["pineappl"] = pineappl.__version__

        entries = {}
        entries.update(versions)
        entries["lumi_id_types"] = "pdg_mc_ids"
        entries["results_pdf"] = self.pdf
        tools.update_grid_metadata(
            self.grid, self.gridtmp, entries, {"results": results_log}
        )
        self.update_with_tmp()

    def postprocess(self):
        """Postprocess grid(s).

        First run the postrun.sh script (if present),
        then apply metadata to all grids present in the folder.

        The following environment variables will be populated for the
        underlying scripts to use:
            GRID: if only one grid is available, path to the grid
            PINECARD: path to the pinecard folder
        """
        if self.grid.exists():
            os.environ["GRID"] = str(self.grid)
            grids = [self.grid]
        else:
            grids = list(self.dest.glob("*.pineappl*"))

        if not grids:
            raise ValueError("Tried to run postprocessing in a folder with no grids?")

        os.environ["PINECARD"] = self.source.as_posix()

        # apply postrun, if present and executable
        postrun = self.source / "postrun.sh"
        if postrun.exists():
            if os.access(postrun, os.X_OK):
                shutil.copy2(self.source / "postrun.sh", self.dest)
                subprocess.run("./postrun.sh", cwd=self.dest, check=True)
            else:
                raise ValueError(f"Postrun file present but not executable: {postrun}")

        # Add the metadata to *every single grid in the folder*
        # some of these might be just intermediate, apply it anyway
        metadata = self.source / "metadata.txt"
        entries = {}
        if metadata.exists():
            for line in metadata.read_text().splitlines():
                k, v = line.split("=")
                entries[k] = v

        for ext in ["*.pineappl.lz4", "*.pineappl"]:
            for grid in self.dest.glob(ext):
                tools.update_grid_metadata(grid, self.gridtmp, entries)
                self.update_with_tmp(grid)

        # compress if we have a single grid
        if self.grid.exists():
            compressed_path = tools.compress(self.grid)
            if compressed_path.exists():
                self.grid.unlink()
