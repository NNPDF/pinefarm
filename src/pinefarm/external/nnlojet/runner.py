"""Provides a runner for NNLOJET."""

from yaml import safe_load

from .. import interface
from .runcardgen import generate_nnlojet_runcard


class NNLOJET(interface.External):
    """Interface provider for NNLOJET."""

    def __init__(self, pinecard, theorycard, *args, **kwargs):
        super().__init__(pinecard, theorycard, *args, **kwargs)

        pinecard = pinecard.replace("NNLOJET_", "")
        yaml_card = (self.source / pinecard).with_suffix(".yaml")
        # Save the yaml dictionary from the NNLOJET pinecard
        self._yaml_dict = safe_load(yaml_card.open("r"))

    def preparation(self):
        """Run the preparation step for NNLOJET"""
        # Update the yaml card according to the theory
        params = self._yaml_dict["parameters"]

        ckm_first = float(self.theory.get("CKM", "1.0").split()[0])
        if ckm_first != 1.0:
            params["CKM"] = "FULL"

        translate = [("MZ", "MASS[Z]"), ("MW", "MASS[W]")]
        for nnpdf_key, nnlojet_key in translate:
            if nnpdf_key in self.theory:
                params[nnlojet_key] = self.theory[nnpdf_key]

        # Autodiscover scale if possible
        if (scdict := self._yaml_dict.get("scales")) is not None:
            for scale, key in scdict.items():
                if isinstance(key, str) and key.upper() in self.theory:
                    scdict[scale] = self.theory[key.upper()]

        # Select channels according to PTO
        order = self.theory.get("PTO")
        channels = ["LO"]
        if order > 0:
            channels += ["R", "V"]
        if order > 1:
            channels += ["RR", "RV", "VV"]
        if order > 2:
            raise NotImplementedError("N3LO still not working")

        # Generate both the production and warmup runcards
        for warmup in [True, False]:
            _ = generate_nnlojet_runcard(
                self._yaml_dict, channels, output=self.dest, warmup=warmup
            )
        return True

    def run(self):
        """Run the corresponding NNLOJET runcard"""
        raise NotImplementedError("NNLOJET running not implemented outside of dry mode")

    def collect_versions(self) -> dict:
        return {"nnlojet_version": "secret"}

    def generate_pineappl(self):
        print("Not yet")

    def results(self):
        print("Good luck")
