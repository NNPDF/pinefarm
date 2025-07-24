"""Autogeneration of NNLOJET runcards.

Module for the autogeneration of NNLOJET runcards using as input
yaml files containing the NNPDF dataset information.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

import numpy as np
from yaml import safe_load

logger = logging.getLogger(__name__)

HEADER = r"""
!###############################################!
!##                                           ##!
!##     _  ___  ____   ____     ____________  ##!
!##    / |/ / |/ / /  / __ \__ / / __/_  __/  ##!
!##   /    /    / /__/ /_/ / // / _/  / /     ##!
!##  /_/|_/_/|_/____/\____/\___/___/ /_/      ##!
!##                                           ##!
!##  Runcard for NNPDF datasets               ##!
!###############################################!
"""
INDT = "  "  # indentation

# Constants for the combine.ini config file
COMBINE_OUTPUT_FOLDER = "combined"
COMBINE_HEADER = f"""
[Paths]
raw_dir = .
out_dir = {COMBINE_OUTPUT_FOLDER}

"""
COMBINE_FOOTER = """

[Options]
recursive = True
weights = True
trim = (3.5, 0.01)
k-scan = (None, 3, 0.7)
"""


@dataclass
class Histogram:
    """Holds histogram information."""

    name: str
    observable: str
    bins: list
    extra_selectors: dict = None
    pineappl: bool = True
    fac: int = None
    compositions: list[dict] = field(default_factory=list)

    def __post_init__(self):
        # Check for compositeness
        if self.observable.upper() == "COMPOSITE" and not self.compositions:
            raise ValueError("Observable is COMPOSITE but no composition found")
        if self.observable.upper() != "COMPOSITE" and self.compositions:
            raise ValueError(
                f"Composition found but the observable is not 'composite' ({self.observable})"
            )

        # Make the composition into histogram classes
        diggested_composition = []
        for comp in self.compositions:
            diggested_composition.append(
                Histogram(**comp, bins=[None], name=None, pineappl=False)
            )
        self.compositions = diggested_composition

    def histogram_selectors_to_str(self, base_indentation=INDT):
        """Make the histogram selectors into a single string."""
        selectors = [Selector(**i) for i in self.extra_selectors]
        hstr = f"\n{base_indentation}HISTOGRAM_SELECTORS\n"
        hstr += f"\n".join(f"{base_indentation}{INDT}{i.to_str()}" for i in selectors)
        hstr += f"\n{base_indentation}END_HISTOGRAM_SELECTORS\n"
        return hstr

    def to_str(self):
        """Turn the histogram into a NNLOJET-compatible string."""
        hstr = f"{INDT}{self.observable} > {self.name} {self.bins}"

        if self.pineappl:
            hstr += f" grid={self.name}.pine"
        if self.fac is not None:
            hstr += f" fac={self.fac}"

        if self.extra_selectors is not None:
            hstr += self.histogram_selectors_to_str()
        else:
            hstr += "\n"

        for composition in self.compositions:
            hstr += f"{INDT*2}{composition.observable}"
            if composition.fac is not None:
                hstr += f" fac={composition.fac}"
            hstr += composition.histogram_selectors_to_str(base_indentation=INDT * 2)
        if self.compositions:
            hstr += f"{INDT}END_COMPOSITE\n"

        return hstr


@dataclass
class Selector:
    """Holds selector information."""

    observable: str
    min: float = None
    max: float = None

    def to_str(self):  # noqa: D102
        ret = f"{INDT}select {self.observable} "
        if self.min is not None:
            ret += f" min = {self.min}"
        if self.max is not None:
            ret += f" max = {self.max}"
        return ret


@dataclass
class YamlLOJET:
    """Definition of the yaml runcard for sending NNLOJET jobs."""

    runname: str
    process: dict
    channels: dict
    scales: dict = field(default_factory=dict)
    parameters: dict = field(default_factory=dict)
    selectors: list = None
    histograms: list = None
    multi_channel: int = 3
    techcut: float = 1e-7
    pdf: str = "NNPDF40_nnlo_as_01180"
    manual: bool = False

    def __post_init__(self):
        self.histograms = [Histogram(**i) for i in self.histograms]
        self.selectors = [Selector(**i) for i in self.selectors]

    @cached_property
    def channel_names_list(self):
        """List of channels."""
        return list(self.channels.keys())

    def active_channels(self, active_channels=None):
        """Digest active channels.

        Loop over all channels in the yamlcard and check whether
        it correspond to one of the channels in the list `active_channels`
        e.g., if active_channels = [RR, RV], all RRa_n, RRb_n, and RV_n will be accepted
        If active_channels is None, return the whole thing for [LO, R, V, RR, RV, VV]

        Returns a dict  {channel_name: list_of_channels}
        """
        if active_channels is None:
            return self.active_channels(["LO", "R", "V", "RR", "RV", "VV"])

        active_channels = list(active_channels)

        if "NLO" in active_channels:
            active_channels.append("R")
            active_channels.append("V")

        if "NNLO" in active_channels:
            active_channels.append("RR")
            active_channels.append("RV")
            active_channels.append("VV")

        ret = defaultdict(list)

        # Run over all channels
        for channel in self.channel_names_list:
            for level in active_channels:
                level_prefix = f"{level}_"
                if level == "RR":
                    level_prefix = ("RR_", "RRa_", "RRb_")

                if channel.startswith(level_prefix) or channel == level:
                    ret[level].append(channel)

        return ret

    def get_channel_list(self, channel):
        """Generate list of channels."""
        return self.channels[channel]

    @property
    def process_name(self):
        """Get process name."""
        return self.process["proc"]

    def selector_definitions(self):
        """Get definition of selectors."""
        return "\n".join(i.to_str() for i in self.selectors)

    def histogram_definitions(self):
        """Return a string with the definition of all the histograms.

        In general the histogram is defined in the yaml file as a dict with:
            - name
              observable
              bins
              extra_selectors: dict
        """
        return "\n".join(i.to_str() for i in self.histograms)


def parse_input_yaml(yaml_path):
    """Parse the yaml runcard into a YamlLOJET object."""
    if not yaml_path.exists():
        raise FileNotFoundError(f"Yaml file {yaml_path} not found")
    yaml_dict = safe_load(yaml_path.open("r"))
    return YamlLOJET(**yaml_dict)


def _fill_process(process):
    """Fill process options."""
    process_name = process["proc"]
    sqrts = process["sqrts"]
    jet = process.get("jet", "none[0]")  # Can be None
    """Fill process block given the metadata for the process"""
    return f"""
PROCESS  {process_name}
  collider = pp  sqrts = {sqrts}
  jet = {jet}
  decay_type = 1
END_PROCESS
"""


def _fill_run(runname, pdf, mode_line, techcut=1e-7, multi_channel=3):
    """Fil run options."""
    if multi_channel == 0:
        multi_channel = ".false."
    # Note, scale coefficients need to be set to true to fill the grid
    return f"""
RUN  {runname.upper()}
  PDF = {pdf}[0]
  tcut = {techcut}
  scale_coefficients = .true.
  multi_channel = {multi_channel}
  iseed = 1
  {mode_line}
END_RUN
"""


def _fill_parameters(theory_parameters):
    """Fill physical parameters."""
    parameters = {
        "MASS[Z]": 91.1876,
        "WIDTH[Z]": 2.4952,
        "MASS[W]": 80.379,
        "WIDTH[W]": 2.085,
        "SCHEME[alpha]": "Gmu",
        "GF": 1.1663787e-5,
    }

    parameters.update(theory_parameters)
    ptext = "\n".join(f"{i} = {j}" for i, j in parameters.items())

    return f"""
PARAMETERS
{ptext}
END_PARAMETERS
"""


def _fill_selectors(metadata):
    """Fill selectors."""
    return f"""
SELECTORS
{metadata.selector_definitions()}
END_SELECTORS
"""


def _fill_histograms(metadata, empty=True):
    """Create the histograms from the declarative definition."""
    if empty:
        histogram_content = ""
    else:
        histogram_content = metadata.histogram_definitions()

    return f"""
HISTOGRAMS
{histogram_content}
END_HISTOGRAMS
"""


def _fill_scales(scales):
    """Fill in scales."""
    mur = scales.get("mur", 91.2)
    muf = scales.get("muf", 91.2)

    return f"""
SCALES
{INDT}mur = {mur}  muf = {muf}
END_SCALES
"""


def region_str_generator(channel_name):
    """Given the name of the channel, set up the region."""
    order = channel_name.split("_", 1)[0]
    if order.endswith("a"):
        return "region = a"
    elif order.endswith("b"):
        return "region = b"
    return ""


def _fill_channels(channels, region_str=""):
    """Fill channels."""
    return f"""
CHANNELS {region_str}
  {channels}
END_CHANNELS
"""


def generate_runcard(
    metadata: YamlLOJET,
    channel: str,
    runcard_name: str = "runcard",
    is_warmup: bool = False,
    events: int = int(1e4),
    iterations: int = 1,
    output=Path("."),
    runcard_path=None,
):
    """Generate a NNLOJET runcard given the metadata of the run in the folder defined by che channel name.

    The output path of the runcard will be ./channel/runcard_name_{warmup/production}.run.
    """
    region_str = region_str_generator(channel)

    if is_warmup:
        mode_str = "warmup"
    else:
        mode_str = "production"
        if iterations > 1:
            raise ValueError("Only 1 iterations allowed in production")
    mode_line = f"{mode_str} = {events}[{iterations}]"
    channels = metadata.get_channel_list(channel)

    pdf = (
        metadata.pdf
    )  # we can even check whether this needs to be installed before running!

    runcard_text = HEADER

    runcard_text += _fill_process(metadata.process)
    runcard_text += _fill_run(
        metadata.runname,
        pdf,
        mode_line,
        techcut=metadata.techcut,
        multi_channel=metadata.multi_channel,
    )
    runcard_text += _fill_parameters(metadata.parameters)
    runcard_text += _fill_selectors(metadata)
    runcard_text += _fill_histograms(metadata, empty=is_warmup)
    runcard_text += _fill_scales(metadata.scales)
    runcard_text += _fill_channels(channels, region_str=region_str)

    if runcard_path is None:
        channel_dir = output / channel
        channel_dir.mkdir(exist_ok=True)
        runcard_path = channel_dir / f"{runcard_name}_{mode_str}.run"

    runcard_path.write_text(runcard_text)

    logger.info(f"Runcard written to {runcard_path}")

    return runcard_path


## combine.ini generation


def _channel_selection(metadata, channels=None):
    """Generate a selection of channels compatible with the metadata.

    Run over all possible channels in the metadata and add them
    to the combine script in the right combination whenever they are
    selected in the arguments of this function.

    Parameters
    ----------
        metadata: YamlLOJET
            information from th e pinecard
        channels: list(str)
            list of channels to be run
    """
    all_levels = {i.split("_")[0] for i in metadata.channels.keys()}

    lo = ["LO"]
    nlo = ["R", "V"]
    nnlo = ["RR", "RV", "VV", "RRa", "RRb"]

    def is_allowed(l):
        """Return false if the given level is not allowed."""
        if channels is None:
            return True
        if l in channels:
            return True
        if l in ("RRa", "RRb") and ("RR" in channels):
            return True
        return False

    ret = {}
    # Now go over every level and include it in the combine.ini
    # whenever it is both in channels and in the metadata
    if add_lo := all_levels.intersection(lo):
        if all(is_allowed(i) for i in add_lo):
            ret["LO"] = list(add_lo)
    if add_nlo := all_levels.intersection(nlo):
        tmp = list(add_nlo.union(add_lo))
        if all(is_allowed(i) for i in tmp):
            ret["NLO"] = tmp
    if add_nnlo := all_levels.intersection(nnlo):
        tmp = list(add_nnlo.union(add_nlo).union(add_lo))
        if all(is_allowed(i) for i in tmp):
            ret["NNLO"] = tmp
        # Add a exclusive NNLO level for debugging
        if all(is_allowed(i) for i in add_nnlo):
            ret["exclusive_nnlo"] = list(add_nnlo)

    if not ret:
        raise ValueError(f"No channel {channels} found in the pinecard")

    return ret


def _generate_channel_merging(metadata, combinations):
    """Define how subchannels are to be merged.

    Looking at metadata and the list of allowed channels, prepare
    [Parts], [Merge] and [Final].
    """
    allowed_levels = set(np.concatenate(list(combinations.values())))
    merge_dict = metadata.active_channels(active_channels=allowed_levels)

    parts_list = []
    merge_list = []
    for level_name, channel_list in merge_dict.items():
        parts_list.append("\n".join(channel_list))
        merge_list.append(f"{level_name} = " + " + ".join(channel_list))

    ret = "\n[Parts]\n" + "\n".join(parts_list)
    ret += "\n\n[Merge]\n" + "\n".join(merge_list)
    ret += "\n\n[Final]"

    for order, levels in combinations.items():
        if all(l in merge_dict for l in levels):
            ret += f"\n{order} = " + " + ".join(levels)

    return ret


def generate_combine_ini(metadata, channels, output=Path(".")):
    """Generate a NNLOJET combine config file."""
    # Initialize the file
    cini_text = COMBINE_HEADER

    # Define the list of observables
    obs_list = "\n".join([i.name for i in metadata.histograms])
    cini_text += f"\n[Observables]\ncross\n{obs_list}\n"

    # Define which (nnlojet) channels are neded and how they are merged
    combinations = _channel_selection(metadata, channels)
    cini_text += _generate_channel_merging(metadata, combinations)

    cini_text += COMBINE_FOOTER

    (output / "combine.ini").write_text(cini_text)
