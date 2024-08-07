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
    lepton_pid: int
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
        self.convolution_type = self._info.convolution_type

    def run(self):
        """Empty function."""
        pass

    def generate_pineappl(self):
        """Generate the pineappl grid for the integrability observable."""
        ## Generate the grid
        lumi_entries = [(fl, self._info.lepton_pid, w) for fl, w in self._evo2fl]
        luminosities = [pineappl.lumi.LumiEntry(lumi_entries)]
        # Set default parameters
        orders = [pineappl.grid.Order(0, 0, 0, 0)]
        params = pineappl.subgrid.SubgridParams()
        # Initialize and parametrize grid
        grid = pineappl.grid.Grid.create(luminosities, orders, [0.0, 1.0], params)
        grid.set_key_value("convolution_particle_1", str(self._info.hadron_pid))
        grid.set_key_value("convolution_particle_2", str(self._info.lepton_pid))
        grid.set_key_value("runcard", json.dumps(self._info.asdict()))
        grid.set_key_value("lumi_id_types", "pdg_mc_ids")
        grid.set_key_value("convolution_type_1", self.convolution_type)
        grid.set_key_value("convolution_type_2", str(None))
        # Fill grid with x*f(x)
        # use subgrid because fill doesn't work?
        x = self._info.xgrid
        w = np.array(x).reshape((1, -1, 1))
        sg = pineappl.import_only_subgrid.ImportOnlySubgridV1(w, [self._q2], x, x)
        grid.set_subgrid(0, 0, 0, sg)
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
