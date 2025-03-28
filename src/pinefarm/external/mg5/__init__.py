"""Madgraph interface."""

import json
import pathlib
import re
import subprocess

import numpy as np
import pandas as pd
import pineappl

from ... import configs, install, log, tools
from .. import interface
from . import paths

URL = "https://launchpad.net/mg5amcnlo/{major}.0/{major}.{minor}.x/+download/MG5_aMC_v{version}.tar.gz"
"URL template for MG5aMC\\@NLO release"
VERSION = "3.6.2"
"Version in use"
CONVERT_MODEL = """
set auto_convert_model True
import model loop_qcd_qed_sm_Gmu
quit
"""
"Instructions to set the correct model for MG5aMC\\@NLO."


def url():
    """Compute actual download URL."""
    major, minor, _ = VERSION.split(".")
    return URL.format(version=VERSION, major=major, minor=minor)


class Mg5(interface.External):
    """Interface provider."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user_jet_cuts = []
        self.user_lepton_cuts = []
        self.patches = []
        self.tau_min = None

    @property
    def mg5_dir(self):
        """Return output dir."""
        return self.dest / self.name

    @staticmethod
    def install():
        """Execute installer."""
        install.pineappl()
        install.mg5amc()

    @property
    def pdf_id(self):
        """Convert PDF to SetIndex."""
        import lhapdf  # pylint: disable=import-error

        return lhapdf.mkPDF(self.pdf).info().get_entry("SetIndex")

    def run(self):
        """Execute program."""
        # copy the output file to the directory and replace the variables
        output = (self.source / "output.txt").read_text().replace("@OUTPUT@", self.name)
        output_file = self.dest / "output.txt"
        output_file.write_text(output)

        # create output folder
        log.subprocess(
            [str(configs.configs["commands"]["mg5"]), str(output_file)],
            cwd=self.dest,
            out=(self.dest / "output.log"),
        )

        # copy patches if there are any; use xargs to properly signal failures
        for p in self.source.iterdir():
            if p.suffix == ".patch":
                subprocess.run(
                    "patch -p1".split(),
                    input=p.read_text(),
                    text=True,
                    cwd=self.mg5_dir,
                )

        # enforce proper analysis
        # - copy analysis.f
        analysis = (self.source / "analysis.f").read_text()
        (self.mg5_dir / "FixedOrderAnalysis" / f"{self.name}.f").write_text(analysis)
        # - update analysis card
        analysis_card = self.mg5_dir / "Cards" / "FO_analyse_card.dat"
        analysis_card.write_text(
            analysis_card.read_text().replace("analysis_HwU_template", self.name)
        )

        # copy the launch file to the directory and replace the variables
        launch = (self.source / "launch.txt").read_text().replace("@OUTPUT@", self.name)

        # TODO: write a list with variables that should be replaced in the
        # launch file; for the time being we create the file here, but in the
        # future it should be read from the theory database EDIT: now available
        # in self.theory
        variables = json.loads((paths.subpkg.parents[1] / "variables.json").read_text())
        variables["LHAPDF_ID"] = self.pdf_id

        # replace the variables with their values
        for name, value in variables.items():
            launch = launch.replace(f"@{name}@", str(value))

        # finally write launch
        launch_file = self.dest / "launch.txt"
        launch_file.write_text(launch)

        # parse launch file for user-defined cuts
        user_cuts_pattern = re.compile(
            r"^#user_defined_cut set (\w+)\s+=\s+([+-]?\d+(?:\.\d+)?|True|False)$"
        )

        # Load cut type dictionary
        cut_type_file = paths.subpkg / "cut_type.json"
        with open(cut_type_file) as f:
            cut_type_map = json.load(f)

        for line in launch.splitlines():
            if m := user_cuts_pattern.fullmatch(line):
                cut_name, cut_value = m[1], m[2]
                cut_type = cut_type_map.get(cut_name)

                if cut_type == "lepton":
                    self.user_lepton_cuts.append((cut_name, cut_value))
                elif cut_type == "jet":
                    self.user_jet_cuts.append((cut_name, cut_value))
                else:
                    print(
                        f"\033[93m[WARNING]\033[0m Unknown cut type for '{cut_name}', ignoring."
                    )

        # if there are user-defined cuts, implement them
        # we now distinguish between lepton and jet cuts
        mg5_cut_dir = self.mg5_dir / "SubProcesses" / "cuts.f"
        if len(self.user_lepton_cuts) != 0:
            apply_user_cuts(mg5_cut_dir, self.user_lepton_cuts)
        if len(self.user_jet_cuts) != 0:
            apply_user_cuts(mg5_cut_dir, self.user_jet_cuts, jet=True)

        # parse launch file for user-defined minimum tau
        user_taumin_pattern = re.compile(r"^#user_defined_tau_min (.*)")
        user_taumin = None
        for line in launch.splitlines():
            m = re.fullmatch(user_taumin_pattern, line)
            if m is not None:
                try:
                    user_taumin = float(m[1])
                except ValueError:
                    raise ValueError("User defined tau_min is expected to be a number")

        if user_taumin is not None:
            set_tau_min_patch = (
                (paths.patches / "set_tau_min.patch")
                .read_text()
                .replace("@TAU_MIN@", f"{user_taumin}d0")
            )
            (self.dest / "set_tau_min.patch").write_text(set_tau_min_patch)
            self.tau_min = user_taumin
            tools.patch(set_tau_min_patch, self.mg5_dir)

        # parse launch file for other patches
        enable_patches_pattern = re.compile(r"^#enable_patch (.*)")
        enable_patches_list = []
        for line in launch.splitlines():
            m = re.fullmatch(enable_patches_pattern, line)
            if m is not None:
                enable_patches_list.append(m[1])

        if len(enable_patches_list) != 0:
            for patch in enable_patches_list:
                patch_file = paths.patches / patch
                patch_file = patch_file.with_suffix(patch_file.suffix + ".patch")
                if not patch_file.exists():
                    raise ValueError(
                        f"Patch '{patch}' requested, but does not exist in patches folder"
                    )
                self.patches.append(patch)
                tools.patch(patch_file.read_text(), self.mg5_dir)

        # launch run
        log.subprocess(
            [str(configs.configs["commands"]["mg5"]), str(launch_file)],
            cwd=self.dest,
            out=self.dest / "launch.log",
        )

    def generate_pineappl(self):
        """Generate grid."""
        # if rerunning without regenerating, let's remove the already merged
        # grid (it will be soon reobtained)
        if self.timestamp is not None:
            self.grid.unlink()

        # merge the final bins
        mg5_grids = sorted(
            str(p.absolute())
            for p in self.mg5_dir.glob("Events/run_01*/amcblast_obs_*.pineappl")
        )
        # read the first one from file
        grid = pineappl.grid.Grid.read(mg5_grids[0])
        # subsequently merge all the others (disk -> memory)
        for path in mg5_grids[1:]:
            grid.merge_from_file(path)

        # optimize the grids
        grid.optimize()

        # add results to metadata
        runcard = next(
            iter(self.mg5_dir.glob("Events/run_01*/run_01*_tag_1_banner.txt"))
        )
        grid.set_key_value("runcard", runcard.read_text())
        # add generated cards to metadata
        grid.set_key_value("output.txt", (self.dest / "output.txt").read_text())
        grid.set_key_value("launch.txt", (self.dest / "launch.txt").read_text())
        # add patches and cuts used to metadata
        grid.set_key_value("patches", "\n".join(self.patches))
        grid.set_key_value(
            "tau_min", str(self.tau_min) if self.tau_min is not None else ""
        )
        grid.set_key_value(
            "user_lepton_cuts",
            "\n".join(f"{var}={value}" for var, value in self.user_lepton_cuts),
        )
        grid.set_key_value(
            "user_jet_cuts",
            "\n".join(f"{var}={value}" for var, value in self.user_jet_cuts),
        )

        grid.write(str(self.grid))

    def results(self):
        """Collect PDF results."""
        madatnlo = next(
            iter(self.mg5_dir.glob("Events/run_01*/MADatNLO.HwU"))
        ).read_text()
        table = filter(
            lambda line: re.match("^  [+-]", line) is not None, madatnlo.splitlines()
        )
        df = pd.DataFrame(
            np.array([[float(x) for x in line.split()] for line in table])
        )
        # start column from 1
        df.columns += 1
        df["result"] = df[3]
        df["error"] = df[4]
        df["sv_min"] = df[6]
        df["sv_max"] = df[7]

        return df

    def collect_versions(self):
        """Collect MG5aMC version info from static VERSION file."""
        versions = {}
        mg5_path = configs.configs["paths"]["mg5amc"]
        version_file = mg5_path / "VERSION"  # assuming mg5_path is already a Path

        if version_file.exists():
            versions["mg5amc_version"] = version_file.read_text().strip()
        else:
            print(f"Warning: VERSION file not found at {version_file}")
            versions["mg5amc_version"] = None

        return versions


def find_marker_position(insertion_marker, contents):
    """Find in file."""
    marker_pos = -1

    for lineno, value in enumerate(contents):
        if insertion_marker in value:
            marker_pos = lineno
            break

    if marker_pos == -1:
        raise ValueError(
            "Error: could not find insertion marker `{insertion_marker}` in cut file `{file_path}`"
        )

    return marker_pos


def apply_user_cuts(cuts_file, user_cuts, jet=False):
    """Apply a user defined cut, patching a suitable cuts file."""
    with open(cuts_file) as fd:
        contents = fd.readlines()

    # insert variable declaration
    variable_marke_name = (
        "logical function passcuts_jets" if jet else "logical function passcuts_leptons"
    )
    rel_pos = 9 if jet else 7
    marker_pos = find_marker_position(variable_marke_name, contents)
    marker_pos = marker_pos + rel_pos

    cut_variable_path = (
        paths.cuts_variables / "jet" if jet else paths.cuts_variables / "lepton"
    )
    for fname in cut_variable_path.iterdir():
        name = fname.stem
        if any(i[0].startswith(name) for i in user_cuts):
            contents.insert(marker_pos, fname.read_text())

    # where to place the cuts
    cut_marker_str = (
        "c Apply the jet cuts" if jet else "c apply the charged lepton cuts"
    )
    marker_pos = find_marker_position(cut_marker_str, contents)
    # skip some lines with comments
    marker_pos = marker_pos + 1
    # insert an empty line
    contents.insert(marker_pos - 1, "\n")

    cut_code_path = paths.cuts_code / "jet" if jet else paths.cuts_code / "lepton"
    for name, value in reversed(user_cuts):
        # map to fortran syntax
        if value == "True":
            value = ".true."
        elif value == "False":
            value = ".false."
        else:
            try:
                float(value)
            except ValueError:
                raise ValueError(f"Error: format of value `{value}` not understood")

            value = value + "d0"

        code = (cut_code_path / f"{name}.f").read_text().format(value)
        contents.insert(marker_pos, code)

    with open(cuts_file, "w") as fd:
        fd.writelines(contents)
