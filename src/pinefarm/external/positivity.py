"""Positivity interface."""

import json

import numpy as np
import pandas as pd
import pineappl
import yaml

from .. import configs
from . import interface


class Positivity(interface.External):
    """Interface provider."""

    kind = "Positivity"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self):
        """Open configuration."""
        with open(
            configs.configs["paths"]["runcards"] / self.name / "positivity.yaml"
        ) as o:
            self.runcard = yaml.safe_load(o)

    def generate_pineappl(self):
        """Generate grid."""
        self.xgrid = self.runcard["xgrid"]
        self.lepton_pid = self.runcard["lepton_pid"]
        self.pid = self.runcard["pid"]
        self.q2 = self.runcard["q2"]
        self.hadron_pid = self.runcard["hadron_pid"]
        self.convolution_type = self.runcard.get("convolution_type", "UnpolPDF")

        # init pineappl objects
        lumi_entries = [pineappl.lumi.LumiEntry([(self.pid, self.lepton_pid, 1.0)])]
        orders = [pineappl.grid.Order(0, 0, 0, 0)]
        bins = len(self.xgrid)
        bin_limits = list(map(float, range(0, bins + 1)))
        # subgrid params - default is just sufficient
        params = pineappl.subgrid.SubgridParams()
        # inti grid
        grid = pineappl.grid.Grid.create(lumi_entries, orders, bin_limits, params)
        limits = []
        # add each point as a bin
        for bin_, x in enumerate(self.xgrid):
            # keep DIS bins
            limits.append((self.q2, self.q2))
            limits.append((x, x))
            # delta function
            array = np.zeros(len(self.xgrid))
            array[bin_] = x
            # create and set
            subgrid = pineappl.import_only_subgrid.ImportOnlySubgridV1(
                array[np.newaxis, :, np.newaxis],
                [self.q2],
                self.xgrid,
                [1.0],
            )
            grid.set_subgrid(0, bin_, 0, subgrid)
        # set the correct observables
        normalizations = [1.0] * bins
        remapper = pineappl.bin.BinRemapper(normalizations, limits)
        grid.set_remapper(remapper)

        # set the initial state PDF ids for the grid
        grid.set_key_value("convolution_particle_1", str(self.hadron_pid))
        grid.set_key_value("convolution_particle_2", str(self.lepton_pid))
        grid.set_key_value("runcard", json.dumps(self.runcard))
        grid.set_key_value("lumi_id_types", "pdg_mc_ids")
        grid.set_key_value("convolution_type_1", self.convolution_type)
        grid.set_key_value("convolution_type_2", str(None))
        grid.optimize()
        grid.write(str(self.grid))

    def results(self):
        """Apply PDF to grid."""
        import lhapdf  # pylint: disable=import-error

        pdf = lhapdf.mkPDF(self.pdf)
        d = {
            "result": [pdf.xfxQ2(self.pid, x, self.q2) for x in self.xgrid],
            "error": [1e-15] * len(self.xgrid),
            "sv_min": [
                np.amin(
                    [
                        pdf.xfxQ2(self.pid, x, 0.25 * self.q2),
                        pdf.xfxQ2(self.pid, x, self.q2),
                        pdf.xfxQ2(self.pid, x, 4.0 * self.q2),
                    ]
                )
                for x in self.xgrid
            ],
            "sv_max": [
                np.amax(
                    [
                        pdf.xfxQ2(self.pid, x, 0.25 * self.q2),
                        pdf.xfxQ2(self.pid, x, self.q2),
                        pdf.xfxQ2(self.pid, x, 4.0 * self.q2),
                    ]
                )
                for x in self.xgrid
            ],
        }
        results = pd.DataFrame(data=d)

        return results

    def collect_versions(self):
        """No additional programs involved."""
        return {}
