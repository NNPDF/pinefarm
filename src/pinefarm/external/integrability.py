"""Integrability interface."""

import dataclasses
import json
import typing

import numpy as np
import pandas as pd
import pineappl
import yaml
from eko import basis_rotation as br

from . import interface

_RUNCARD = "integrability.yaml"


def evolution_to_flavour(evol_fl):
    """Use eko to transform an evolution pid (>100) to flavour basis in a pineappl-usable way (flavour, weight)."""
    if evol_fl < 100:
        return [(evol_fl, 1.0)]
    idx = br.evol_basis_pids.index(evol_fl)
    row = br.rotate_flavor_to_evolution[idx]
    lumis = []
    for i, w in enumerate(row):
        if w != 0.0:
            lumis.append((br.flavor_basis_pids[i], w))
    return lumis


@dataclasses.dataclass
class _IntegrabilityRuncard:
    hadron_pid: int
    flavour: int
    xgrid: typing.List[float]
    convolution_type: typing.Optional[str] = "UnpolPDF"

    def asdict(self):
        return dataclasses.asdict(self)


class Integrability(interface.External):
    """Interface provider."""

    kind = "Integrability"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        input_card = self.source / _RUNCARD
        yaml_dict = yaml.safe_load(input_card.open("r", encoding="utf-8"))
        self._q2 = np.power(self.theory["Q0"], 2)
        self._info = _IntegrabilityRuncard(**yaml_dict)
        self._evo2fl = evolution_to_flavour(self._info.flavour)
        self.polarized = self._info.convolution_type == "PolPDF"

    def run(self):
        """Empty function."""
        pass

    def generate_pineappl(self):
        """Generate the pineappl grid for the integrability observable."""
        xgrid = np.array(self._info.xgrid)
        bins_length = len(xgrid)
        bin_limits = [float(i) for i in range(0, bins_length + 1)]

        ## Generate the grid
        channels = [([fl], w) for fl, w in self._evo2fl]
        channels = [pineappl.boc.Channel(channels)]
        # Set default parameters
        orders = [pineappl.boc.Order(0, 0, 0, 0, 0)]
        convolution_types = pineappl.convolutions.ConvType(
            polarized=self.polarized, time_like=False
        )
        convolutions = [
            pineappl.convolutions.Conv(convolution_types=convolution_types, pid=2212)
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
                min=1,
                max=1e2,
                nodes=50,
                order=3,
                reweight_meth=pineappl.interpolation.ReweightingMethod.NoReweight,
                map=pineappl.interpolation.MappingMethod.ApplGridH0,
                interpolation_meth=pineappl.interpolation.InterpolationMethod.Lagrange,
            ),  # Interpolation on the Scale
            pineappl.interpolation.Interp(
                min=1e-9,
                max=1,
                nodes=40,
                order=3,
                reweight_meth=pineappl.interpolation.ReweightingMethod.ApplGridX,
                map=pineappl.interpolation.MappingMethod.ApplGridF2,
                interpolation_meth=pineappl.interpolation.InterpolationMethod.Lagrange,
            ),  # Interpolation on momentum fraction x
        ]
        # Initialize and parametrize grid
        grid = pineappl.grid.Grid(
            pid_basis=pineappl.pids.PidBasis.Evol,
            channels=channels,
            orders=orders,
            bins=bin_limits,
            convolutions=convolutions,
            interpolations=interpolations,
            kinematics=kinematics,
            scale_funcs=scale_funcs,
        )
        subgrid = pineappl.subgrid.ImportSubgridV1(
            array=np.full((1, xgrid.size), xgrid),
            node_values=[[self._q2], xgrid],
        )
        grid.set_subgrid(0, 0, 0, subgrid.into())

        limits = [[(self._q2, self._q2), (xgrid, xgrid)]]

        # set the correct observables
        normalizations = [1.0] * bins_length
        bin_configs = pineappl.boc.BinsWithFillLimits.from_limits_and_normalizations(
            limits=limits,
            normalizations=normalizations,
        )
        grid.set_bwfl(bin_configs)

        # set the initial state PDF ids for the grid
        grid.set_metadata(
            "runcard",
            json.dumps(self._info.asdict()),
        )

        # dump file
        grid.optimize()
        grid.write(self.grid)

    def collect_versions(self):
        """Add the version defined by this file."""
        return {"integrability_version": "1.0"}

    def results(self):
        """Apply PDF to grid."""
        import lhapdf  # pylint: disable=import-error

        pdf = lhapdf.mkPDF(self.pdf)
        final_result = 0.0
        q2 = self._q2 * np.ones_like(self._info.xgrid)

        for fl, w in self._evo2fl:
            final_result += w * np.sum(pdf.xfxQ2(fl, self._info.xgrid, q2))

        final_cv = [final_result]

        d = {
            "result": final_cv,
            "error": np.zeros_like(final_cv),
            "sv_min": np.zeros_like(final_cv),
            "sv_max": np.zeros_like(final_cv),
        }
        return pd.DataFrame(data=d)
