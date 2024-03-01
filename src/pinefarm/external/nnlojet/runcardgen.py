"""
    Module for the autogeneration of NNLOJET runcards using as input
    yaml files containing the NNPDF dataset information
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

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


@dataclass
class Histogram:
    name: str
    observable: str
    bins: list
    extra_selectors: dict = None
    pineappl: bool = True

    def to_str(self):
        hstr = f"{INDT}{self.observable} > {self.name} {self.bins}"
        if self.pineappl:
            hstr += " grid=pine"

        if self.extra_selectors is not None:
            hstr += f"\n{INDT}HISTOGRAM_SELECTORS\n{INDT*2}"
            hstr += f"\n{INDT*2}".join(str(i) for i in self.extra_selectors)
            hstr += f"\n{INDT}END_HISTOGRAM_SELECTORS\n"
        return hstr


@dataclass
class Selector:
    observable: str
    min: float = None
    max: float = None

    def to_str(self):
        ret = f"{INDT}select {self.observable} "
        if self.min is not None:
            ret += f" min = {self.min}"
        if self.max is not None:
            ret += f" max = {self.max}"
        return ret


@dataclass
class YamlLOJET:
    """Definition of the yaml runcard for sending NNLOJET jobs"""

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

    def __post_init__(self):
        self.histograms = [Histogram(**i) for i in self.histograms]
        self.selectors = [Selector(**i) for i in self.selectors]

    @cached_property
    def channel_names_list(self):
        return list(self.channels.keys())

    def active_channels(self, active_channels=None):
        """Loop over all channels in the yamlcard and check whether
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
        return self.channels[channel]

    @property
    def process_name(self):
        return self.process["proc"]

    def selector_definitions(self):
        return "\n".join(i.to_str() for i in self.selectors)

    def histogram_definitions(self):
        """Return a string with the definition of all the histograms

        In general the histogram is defined in the yaml file as a dict with:
            - name
              observable
              bins
              extra_selectors: dict
        """
        return "\n".join(i.to_str() for i in self.histograms)


def parse_input_yaml(yaml_path):
    if not yaml_path.exists():
        raise FileNotFoundError(f"Yaml file {yaml_path} not found")
    yaml_dict = safe_load(yaml_path.open("r"))
    return YamlLOJET(**yaml_dict)


def _fill_process(process):
    process_name = process["proc"]
    sqrts = process["sqrts"]
    """Fill process block given the metadata for the process"""
    return f"""
PROCESS  {process_name}
  collider = pp  sqrts = {sqrts}
  jet = none[0]
  decay_type = 1
END_PROCESS
"""


def _fill_run(runname, pdf, mode_line, techcut=1e-7, multi_channel=3):
    if multi_channel == 0:
        multi_channel = ".false."
    return f"""
RUN  {runname.upper()}
  PDF = {pdf}[0]
  tcut = {techcut}
  scale_coefficients = .true.
  multi_channel = {multi_channel}
  iseed = 1
  phase_space = qT
  {mode_line}
END_RUN
"""


def _fill_parameters(theory_parameters):
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
    return f"""
SELECTORS
{metadata.selector_definitions()}
END_SELECTORS
"""


def _fill_histograms(metadata, empty=True):
    """Create the histograms from the declarative definition"""
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
    mur = scales.get("mur", 91.2)
    muf = scales.get("muf", 91.2)

    return f"""
SCALES
{INDT}mur = {mur}  muf = {muf}
END_SCALES
"""


def region_str_generator(channel_name):
    """Given the name of the channel, set up the region"""
    order = channel_name.split("_", 1)[0]
    if order.endswith("a"):
        return "region = a"
    elif order.endswith("b"):
        return "region = b"
    return ""


def _fill_channels(channels, region_str=""):
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
):
    """Generate a NNLOJET runcard given the metadata of the run in the folder defined by che channel name
    The output path of the runcard will be ./channel/runcard_name_{warmup/production}.run
    """

    channel_dir = output / channel
    channel_dir.mkdir(exist_ok=True)

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

    runcard_path = channel_dir / f"{runcard_name}_{mode_str}.run"
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
    runcard_path.write_text(runcard_text)

    logger.info(f"Runcard written to {runcard_path}")

    return runcard_path


def generate_nnlojet_runcard(yamlinfo, channels=("LO",), output=Path(".")):
    """Generate a nnlojet runcard from a yaml pinecard"""
    yaml_metadata = YamlLOJET(**yamlinfo)

    output.mkdir(exist_ok=True, parents=True)

    runcards = []
    for channel in channels:
        runcards.append(generate_runcard(yaml_metadata, channel, output=output))
    return runcards
