"""Provides a runner for NNLOJET."""

import subprocess as sp
import sys

from yaml import safe_load

from .. import interface
from .runcardgen import generate_nnlojet_runcard


class NNLOJET(interface.External):
    """Interface provider for NNLOJET."""

    def __init__(self, pinecard, theorycard, *args, **kwargs):
        super().__init__(pinecard, theorycard, *args, **kwargs)

        pinecard = pinecard.replace("NNLOJET_", "")
        yaml_card = (self.source / pinecard).with_suffix(".yaml")
        yaml_dict = safe_load(yaml_card.open("r"))

        # Update the yaml card according to the theory
        params = yaml_dict["parameters"]

        ckm_first = float(theorycard.get("CKM", "1.0").split()[0])
        if ckm_first != 1.0:
            params["CKM"] = "FULL"

        translate = [("MZ", "MASS[Z]"), ("MW", "MASS[W]")]
        for nnpdf_key, nnlojet_key in translate:
            if nnpdf_key in theorycard:
                params[nnlojet_key] = theorycard[nnpdf_key]

        # Autodiscover scale if possible
        if "scales" in yaml_dict:
            scdict = yaml_dict["scales"]
            for scale, key in scdict.items():
                if isinstance(key, str) and key.upper() in theorycard:
                    scdict[scale] = theorycard[key.upper()]

        # Select channels according to PTO
        order = theorycard.get("PTO")
        channels = ["LO"]
        if order > 0:
            channels += ["R", "V"]
        if order > 1:
            channels += ["RR", "RV", "VV"]
        if order > 2:
            raise NotImplementedError("N3LO still not working")

        self._nnlojet_runcards = generate_nnlojet_runcard(
            yaml_dict, channels, output=self.dest
        )

    def run(self):
        """Run the corresponding NNLOJET runcard"""
        print(f"NNLOJET running not implemented, but you can find the NNLOJET runcards at:\n> {self.dest}")
        sys.exit(-1)
#         for runcard in self._nnlojet_runcards:
#             # Exit regardless of whether there's a NNLOJET executable for now
#             try:
#                 sp.run(["NNLOJET", "-run", runcard.name], cwd=self.dest, check=True)
#             except FileNotFoundError:
#                 print(
#                     f"NNLOJET executable not found, but you can find the NNLOJET runcards at:\n> {self.dest}"
#                 )
#                 sys.exit(-1)

    def collect_versions(self) -> dict:
        return {"nnlojet_version": "secret"}

    def generate_pineappl(self):
        print("Not yet")

    def results(self):
        print("Good luck")
