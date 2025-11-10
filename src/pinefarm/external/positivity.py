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

    def read_kinematics(self):
        """Read kinematics from runcard."""
        if "kinematics" in self.runcard:
            kinematics = self.runcard["kinematics"]
            xgrid = np.array([point["x"] for point in kinematics])
            q2grid = np.array([point["q2"] for point in kinematics])
        else:
            xgrid = np.array(self.runcard["xgrid"])
            q2 = self.runcard["q2"]
            q2grid = np.full_like(xgrid, q2)
        return xgrid, q2grid

    def generate_pineappl(self):
        """Generate grid."""
        self.xgrid, self.q2grid = self.read_kinematics()
        self.pid = self.runcard["pid"]
        self.hadron_pid = self.runcard["hadron_pid"]
        self.convolution_type = self.runcard.get("convolution_type", "UnpolPDF")

        bins_length = len(self.xgrid)
        bin_limits = [float(i) for i in range(0, bins_length + 1)]
        polarized = self.convolution_type == "PolPDF"

        # Instantiate the objecs required to construct a new Grid
        channels = [pineappl.boc.Channel([([self.pid], 1.0)])]
        orders = [pineappl.boc.Order(0, 0, 0, 0, 0)]
        convolution_types = pineappl.convolutions.ConvType(
            polarized=polarized, time_like=False
        )
        convolutions = [
            pineappl.convolutions.Conv(
                convolution_types=convolution_types, pid=self.hadron_pid
            )
        ]
        kinematics = [pineappl.boc.Kinematics.Scale(0), pineappl.boc.Kinematics.X(0)]
        scale_funcs = pineappl.boc.Scales(
            ren=pineappl.boc.ScaleFuncForm.Scale(0),
            fac=pineappl.boc.ScaleFuncForm.Scale(0),
            frg=pineappl.boc.ScaleFuncForm.NoScale(0),
        )
        bin_limits = pineappl.boc.BinsWithFillLimits.from_fill_limits(
            fill_limits=bin_limits
        )
        interpolations = [
            pineappl.interpolation.Interp(
                min=10,
                max=1e3,
                nodes=50,
                order=3,
                reweight_meth=pineappl.interpolation.ReweightingMethod.NoReweight,
                map=pineappl.interpolation.MappingMethod.ApplGridH0,
                interpolation_meth=pineappl.interpolation.InterpolationMethod.Lagrange,
            ),  # Interpolation on the Scale
            pineappl.interpolation.Interp(
                min=1e-5,
                max=1,
                nodes=40,
                order=3,
                reweight_meth=pineappl.interpolation.ReweightingMethod.ApplGridX,
                map=pineappl.interpolation.MappingMethod.ApplGridF2,
                interpolation_meth=pineappl.interpolation.InterpolationMethod.Lagrange,
            ),  # Interpolation on momentum fraction x
        ]

        grid = pineappl.grid.Grid(
            pid_basis=pineappl.pids.PidBasis.Pdg,
            channels=channels,
            orders=orders,
            bins=bin_limits,
            convolutions=convolutions,
            interpolations=interpolations,
            kinematics=kinematics,
            scale_funcs=scale_funcs,
        )

        limits = []
        # add each point as a bin
        for bin_, (x, q2) in enumerate(zip(self.xgrid, self.q2grid)):
            # keep DIS bins
            limits.append([(q2, q2), (x, x)])
            # Fill the subgrid with delta functions
            array_subgrid = np.zeros((1, self.xgrid.size))
            array_subgrid[0][bin_] = x
            # create and set the subgrid
            subgrid = pineappl.subgrid.ImportSubgridV1(
                array=array_subgrid,
                node_values=[self.q2grid, self.xgrid],
            )
            grid.set_subgrid(0, bin_, 0, subgrid.into())
        # set the correct observables
        normalizations = [1.0] * bins_length
        bin_configs = pineappl.boc.BinsWithFillLimits.from_limits_and_normalizations(
            limits=limits,
            normalizations=normalizations,
        )
        grid.set_bwfl(bin_configs)

        # set the initial state PDF ids for the grid
        grid.set_metadata("runcard", json.dumps(self.runcard))

        # dump file
        grid.optimize()
        grid.write(self.grid)

    def results(self):
        """Apply PDF to grid."""
        import lhapdf  # pylint: disable=import-error

        pdf = lhapdf.mkPDF(self.pdf)
        d = {
            "result": [
                pdf.xfxQ2(self.pid, x, q2) for (x, q2) in zip(self.xgrid, self.q2grid)
            ],
            "error": [1e-15] * len(self.xgrid),
            "sv_min": [
                np.amin(
                    [
                        pdf.xfxQ2(self.pid, x, 0.25 * q2),
                        pdf.xfxQ2(self.pid, x, q2),
                        pdf.xfxQ2(self.pid, x, 4.0 * q2),
                    ]
                )
                for (x, q2) in zip(self.xgrid, self.q2grid)
            ],
            "sv_max": [
                np.amax(
                    [
                        pdf.xfxQ2(self.pid, x, 0.25 * q2),
                        pdf.xfxQ2(self.pid, x, q2),
                        pdf.xfxQ2(self.pid, x, 4.0 * q2),
                    ]
                )
                for (x, q2) in zip(self.xgrid, self.q2grid)
            ],
        }
        results = pd.DataFrame(data=d)

        return results

    def collect_versions(self):
        """No additional programs involved."""
        return {}
