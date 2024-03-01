"""
    Read up all important information form an NNPDF dataset

    The selector generation is very flaky and is (mostly) up to the user for now
    - histogram with selectors
    histograms:
        name: test
        observable: ptz
        bins: [10, 20, 40]
        extra_selectors:
            - "reject abs_ylp min = 1.37 max = 1.52"
            - "reject abs_ylm min = 1.37 max = 1.52"
"""

from pathlib import Path

import numpy as np
from ruamel.yaml import YAML, CommentedMap
from validphys.api import API
from validphys.datafiles import path_vpdata
from validphys.theorydbutils import fetch_theory

# set-up the yaml reader
yaml = YAML(pure=True)
yaml.default_flow_style = False
yaml.indent(sequence=4, offset=2, mapping=4)


def _df_to_bins(dataframe):
    """Convert a dataframe containing min/mid/max for some kin variable
    into a list of bins as NNLOJET understands it"""
    bins = dataframe["min"].tolist()
    bins.append(dataframe["max"].tolist()[-1])
    return bins


def _nnlojet_observable(observable, process):
    """Try to automatically understand the NNLOJET observables given the NNPDF process and obs"""
    if observable == "y":
        if process.upper().startswith("Z"):
            return "yz"
        if process.upper().startswith("WP") and not process.upper().endswith("J"):
            return "ylp"
        if process.upper().startswith("WM") and not process.upper().endswith("J"):
            return "ylm"
    if observable == "pt":
        if process.upper().startswith("Z"):
            return "ptz"
        if process.upper().startswith("W"):
            return "ptw"
    raise ValueError(f"Observable {observable} not recognized for process {process}")


def select_selectors(experiment, process):
    """A selection of default selectors to be selected
    depending on the selected experiment"""
    if experiment == "LHCB":
        lhcb_ops = [
            {"observable": "abs_ylp", "min": 2.0, "max": 4.5},
        ]
        if process.startswith("Z"):
            lhcb_ops += [
                {"observable": "ptl2", "min": 20},
                {"observable": "yz", "min": 2.0, "max": 4.5},
                {"observable": "mll", "min": 60, "max": 120},
                {"observable": "abs_ylm", "min": 2.0, "max": 4.5},
            ]
        elif process.startswith("WP"):
            lhcb_ops += [
                {"observable": "ptlp", "min": 20},
            ]
        return lhcb_ops


def generate_pinecard_from_nnpdf(nnpdf_dataset, scale="mz", output_path="."):
    """Generate a NNLOJET pinecard from an NNPDF dataset"""
    commondata = API.commondata(dataset_input={"dataset": nnpdf_dataset})
    metadata = commondata.metadata

    # Define some placeholders which need to be manually modified
    ret = {
        "runname": nnpdf_dataset,
        "process": {"proc": "ZJ", "sqrts": 13000},
        "pdf": "NNPDF40_nnlo_as_01180",
        "techcut": 1e-7,
        "histograms": [],
        "multi_channel": 0,
        "channels": {
            "LO": "LO",
            "R": "R",
            "V": "V",
            "RR": "RR",
            "RV": "RV",
            "VV": "VV",
        },
        "parameters": {
            "MASS[Z]": 91.1876,
            "MASS[W]": 80.379,
            "WIDTH[Z]": 2.4952,
            "WIDTH[W]": 2.085,
            "SCHEME[alpha]": "Gmu",
            "GF": "1.1663787d-5",
        },
    }

    # Load the kinematic information
    kin_df = metadata.load_kinematics(drop_minmax=False)

    # Autoguess the energy
    if "sqrts" in kin_df:
        sqrts = kin_df["sqrts"]["mid"].tolist()[0]
    else:
        print("Warning: sqrts not found")
        sqrts = None
    ret["process"]["sqrts"] = sqrts

    # Try to autoguess the process
    proc = metadata.process.replace("Z0", "Z")
    proc = proc.replace("WPWM", "WP")
    ret["process"]["proc"] = proc

    # Either we are looking at some rapidity or pt
    # Let's not deal with 2D... for now
    kin_variables = kin_df.columns.get_level_values(0)

    accepted_vars = {"y", "etay", "eta", "pT", "pT2"}
    hist_var = list(accepted_vars.intersection(kin_variables))[0]

    histo_bins = _df_to_bins(kin_df[hist_var])

    if hist_var == "pT2":
        histo_bins = [np.sqrt(i) for i in histo_bins]
        hist_var = "pT"

    is_normalized = metadata.theory.operation.lower() == "ratio"

    # TODO: for 2-D distributions we will need to loop here over unique 'figure_by' values
    ret["histograms"] = [
        {
            "name": hist_var,
            "observable": _nnlojet_observable("y", proc),
            "bins": histo_bins,
        }
    ]

    if is_normalized:
        print(
            "\033[91m [WARNING] \033[0m This dataset is probably normalized, you might be missing the runcard for the fiducial cross section"
        )

    # Now it is time to load the theory information!
    nnpdf_theory = fetch_theory(path_vpdata / "theory.db", 708)

    # And go over the pair of names NNPDF - NNLOJET
    name_pairs = [("MW", "MASS[W]"), ("MZ", "MASS[Z]"), ("GF", "GF")]
    for nnpdf_k, nnlojet_k in name_pairs:
        ret["parameters"][nnlojet_k] = nnpdf_theory[nnpdf_k]

    ckm = nnpdf_theory["CKM"].split()
    if float(ckm[0]) == 1:
        ret["parameters"] = "FULL"

    if scale.lower() == "mz":
        scale = ret["parameters"]["MASS[Z]"]
    else:
        scale = scale

    ret["scales"] = {"mur": scale, "muf": scale}
    ret["selectors"] = select_selectors(metadata.experiment, proc)

    # Prepare the metadata for the data
    hepdata = metadata._parent.hepdata.url
    arxiv = metadata._parent.arXiv.url.split("/")[-1]
    tables = metadata.tables
    data_comment = f"arXiv number: {arxiv}, hepdata entry: {hepdata} (tables: {tables})"

    # Beautify before dumping
    data = CommentedMap(ret)
    for key in ret:
        data.yaml_set_comment_before_after_key(key, before="\n")
    data.yaml_set_start_comment(data_comment)

    opath = Path(output_path)
    opath.mkdir(exist_ok=True, parents=True)

    runcard_name = (opath / nnpdf_dataset.upper()).with_suffix(".yaml")
    yaml.dump(data, runcard_name)

    return runcard_name
