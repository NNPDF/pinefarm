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

from copy import deepcopy

import numpy as np
from ruamel.yaml import YAML, CommentedMap
from validphys.api import API
from validphys.datafiles import path_vpdata
from validphys.theorydbutils import fetch_theory

# set-up the yaml reader
yaml = YAML(pure=True)
yaml.default_flow_style = False
yaml.indent(sequence=4, offset=2, mapping=4)

HISTOGRAM_VARIABLES = {"y", "etay", "eta", "pT", "pT2"}


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


def _generate_metadata(arxiv, hepdata, nnpdf_name, output):
    """Generate a minimal ``metadata.txt`` file"""
    empty_fields = [
        "description",
        "x1_label",
        "x1_label_tex",
        "x2_label",
        "x2_label_tex",
        "x2_unit",
        "y_label",
        "y_label_tex",
        "y_unit",
    ]
    ret = f"""arxiv={arxiv}
hepdata={hepdata}
nnpdf_id={nnpdf_name}
"""
    ret += "=\n".join(empty_fields) + "="
    output.write_text(ret)


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


def _generate_nnlojet_pinecard(runname, process, energy, experiment, histograms):
    """Generate a pinecard for NNLOJET runs from an NNPDF dataset"""
    selectors = select_selectors(experiment, process)
    histograms = deepcopy(histograms)

    if process.startswith("Z0"):
        process = process.replace("Z0", "Z")

    # Digest the histogram variable
    for histo in histograms:
        ob = histo["observable"]
        histo["observable"] = _nnlojet_observable(ob, process)

    ret = {
        "runname": runname,
        "process": {"proc": process, "sqrts": energy},
        "pdf": "NNPDF40_nnlo_as_01180",
        "techcut": 1e-7,
        "histograms": histograms,
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
        "selectors": selectors,
    }
    return ret


def generate_pinecard_from_nnpdf(nnpdf_dataset, scale="mz", output_path="."):
    """Generate a NNLOJET pinecard from an NNPDF dataset"""
    # Load the NNPDF dataset
    commondata = API.commondata(dataset_input={"dataset": nnpdf_dataset})
    metadata = commondata.metadata
    kin_df = metadata.load_kinematics(drop_minmax=False)
    output_runcards = []

    # Put all the information we might need in nicely organized variables
    process = metadata.process
    energy = metadata.cm_energy
    experiment = metadata.experiment

    # Now use the kinematic information to generate histograms
    kin_variables = kin_df.columns.get_level_values(0)

    # TODO: Only one at a time for now
    hist_var = list(HISTOGRAM_VARIABLES.intersection(kin_variables))[0]
    histo_bins = _df_to_bins(kin_df[hist_var])

    if hist_var == "pT2":
        histo_bins = [np.sqrt(i) for i in histo_bins]
        hist_var = "pT"

    histograms = [{"name": hist_var, "observable": hist_var, "bins": histo_bins}]

    is_normalized = metadata.theory.operation.lower() == "ratio"
    if is_normalized:
        print(
            "\033[91m [WARNING] \033[0m This dataset is probably normalized, you might be missing the runcard for the fiducial cross section"
        )

    # Prepare the metadata for the data
    hepdata = metadata._parent.hepdata.url
    arxiv = metadata._parent.arXiv.url.split("/")[-1]
    tables = metadata.tables
    data_comment = f"arXiv number: {arxiv}, hepdata entry: {hepdata} (tables: {tables})"

    # For some NNPDF datasets, different processes/energies might be grouped together
    processes = [process]
    if process.startswith("WPWM"):
        processes = [process.replace("WP", ""), process.replace("WM", "")]
    if process == "DY":
        processes = ["Z0", "WP", "WM"]

    parent_folder = output_path.parent
    base_name = output_path.name

    output_runcards = []
    for proc in processes:
        runname = nnpdf_dataset.replace(process, proc)

        ret = _generate_nnlojet_pinecard(runname, proc, energy, experiment, histograms)
        ret["scales"] = {"mur": scale, "muf": scale}

        # Beautify before dumping
        data = CommentedMap(ret)
        for key in ret:
            data.yaml_set_comment_before_after_key(key, before="\n")
        data.yaml_set_start_comment(data_comment)

        opath = parent_folder / base_name.replace(process, proc)
        opath.mkdir(exist_ok=True, parents=True)

        runcard_name = (opath / runname.upper()).with_suffix(".yaml")
        yaml.dump(data, runcard_name)
        output_runcards.append(runcard_name)

        _generate_metadata(
            arxiv, hepdata, nnpdf_dataset, runcard_name.with_name("metadata.txt")
        )

    return output_runcards
