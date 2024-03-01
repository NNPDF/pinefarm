"""Provides a runner for NNLOJET."""

import subprocess as sp
import sys

from .. import interface
from .runcardgen import generate_nnlojet_runcard


class NNLOJET(interface.External):
    """Interface provider for NNLOJET."""

    def __init__(self, pinecard, theorycard, *args, **kwargs):
        super().__init__(pinecard, theorycard, *args, **kwargs)

        pinecard = pinecard.replace("NNLOJET_", "")
        yaml_card = (self.source / pinecard).with_suffix(".yaml")

        order = theorycard.get("PTO")
        channels = ["LO"]
        if order > 0:
            channels += ["R", "V"]
        if order > 1:
            channels += ["RR", "RV", "VV"]
        if order > 2:
            raise NotImplementedError("N3LO still not working")

        self._nnlojet_runcards = generate_nnlojet_runcard(
            yaml_card, channels, output=self.dest
        )

    def run(self):
        """Run the corresponding NNLOJET runcard"""
        for runcard in self._nnlojet_runcards:
            try:
                sp.run(["NNLOJET", "-run", runcard.name], cwd=self.dest, check=True)
            except FileNotFoundError:
                print(
                    f"NNLOJET executable not found, but you can find the NNLOJET runcards at:\n> {self.dest}"
                )
                sys.exit(-1)

    def collect_versions(self) -> dict:
        return {"nnlojet_version": "secret"}

    def generate_pineappl(self):
        print("Not yet")

    def results(self):
        print("Good luck")
