"""Provides a runner for NNLOJET."""

from yaml import safe_load

from .. import interface
from .runcardgen import YamlLOJET, generate_combine_ini, generate_runcard

# Reasonable default for warmup and production for DY
_DEFAULTS = {
    "warmup": {"iterations": 10, "events": int(5e6)},
    "production": {"iterations": 1, "events": int(1e6)},
}


class NNLOJET(interface.External):
    """Interface provider for NNLOJET."""

    def __init__(self, pinecard, theorycard, *args, **kwargs):
        super().__init__(pinecard, theorycard, *args, **kwargs)

        pinecard = pinecard.replace("NNLOJET_", "")
        yaml_card = (self.source / pinecard).with_suffix(".yaml")
        # Save the yaml dictionary from the NNLOJET pinecard
        self._yaml_dict = safe_load(yaml_card.open("r"))

    def preparation(self):
        """Run the preparation step for NNLOJET."""
        # Update the yaml card according to the theory
        params = self._yaml_dict["parameters"]

        if self.theory.get("CKM", [1.0])[0] != 1.0:
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

        pinedata = YamlLOJET(**self._yaml_dict)
        # Given the allowed channel, generate the possible channel choices
        active_channels = pinedata.active_channels(channels)

        # Generate both the production and warmup runcards with reasonable defaults
        self.dest.mkdir(exist_ok=True, parents=True)
        for level_name, level_channels in active_channels.items():
            print(f"Preparing {len(level_channels)} runcards for {level_name}")
            for mode in ["warmup", "production"]:
                nev = _DEFAULTS[mode]["events"]
                nit = _DEFAULTS[mode]["iterations"]
                for channel in level_channels:
                    is_warmup = mode == "warmup"
                    _ = generate_runcard(
                        pinedata,
                        channel,
                        output=self.dest,
                        is_warmup=is_warmup,
                        events=nev,
                        iterations=nit,
                    )

        generate_combine_ini(pinedata, active_channels, self.dest)
        return True

    def run(self):
        """Run the corresponding NNLOJET runcard."""
        raise NotImplementedError("NNLOJET running not implemented outside of dry mode")

    def collect_versions(self) -> dict:
        """NNLOJET version."""
        return {"nnlojet_version": "secret"}

    def generate_pineappl(self):
        """Not implemented."""
        print("Not yet")

    def results(self):
        """Not implemented."""
        print("Good luck")
