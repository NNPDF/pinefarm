"""
Read up all important information form an NNPDF dataset.

The selector generation is very flaky and is (mostly) up to the user for now.

Some examples:

```yaml
    - histogram with selectors
    histograms:
        name: test
        observable: ptz
        bins: [10, 20, 40]
        extra_selectors:
            - "reject abs_ylp min = 1.37 max = 1.52"
            - "reject abs_ylm min = 1.37 max = 1.52"
```
"""

from copy import deepcopy

import numpy as np
from nnpdf_data import load_dataset_metadata
from ruamel.yaml import YAML, CommentedMap

# set-up the yaml reader
yaml = YAML(pure=True)
yaml.default_flow_style = False
yaml.indent(sequence=4, offset=2, mapping=4)

HISTOGRAM_VARIABLES = {"y", "etay", "eta", "pT", "pT2", "M2"}


def _legacy_nnpdf_translation(df, proc_type):
    """When reading variables with k1/k2/k3 tries to figure out to which variables it corresponds."""
    from validphys.filters import KIN_LABEL  # pylint: disable=E0401

    new_vars = list(KIN_LABEL[proc_type])
    # Reorganize a bit the names to avoid extra problems
    if "M_ll" in new_vars:
        new_vars[new_vars.index("M_ll2")] = "M2"
    df.columns = df.columns.set_levels(new_vars, level=0)


def _df_to_bins(dataframe):
    """NNPDF kin dataframe to list of bins.

    Convert a dataframe containing min/mid/max for some kin variable
    into a list of bins as NNLOJET understands it.
    """
    # If the NNPDF dataset has been implemented recently
    # we will have min/max
    # otherwise we have only mid and have to trick this
    if np.allclose(dataframe["min"], dataframe["max"]):
        # Fake min/max and hope for the best
        mid_points = dataframe["mid"].values
        shifts = np.diff(mid_points) / 2.0
        bins = mid_points[:-1] + shifts
        # Assume that the shift in the first and last points
        # is the same as the second and next-to-last
        fpo = [mid_points[0] - shifts[0]]
        lpo = [mid_points[-1] + shifts[-1]]
        return np.concatenate([fpo, bins, lpo])

    # Couple maxs and mins, assuming no overlap between bins...
    all_bins = np.concatenate([dataframe["min"], dataframe["max"]])
    return np.unique(all_bins)


def _1d_histogram(kin_df, hist_var):
    """Prepare the histogram for a 1d distribution."""
    histo_bins = _df_to_bins(kin_df[hist_var])

    if hist_var == "pT2":
        histo_bins = np.sqrt(histo_bins)
        hist_var = "pT"

    if hist_var == "M2":
        histo_bins = np.sqrt(histo_bins)
        hist_var = "M"

    # Don't do more than 3 decimals
    histo_bins = np.round(histo_bins, decimals=3).tolist()

    return {"name": hist_var, "observable": hist_var, "bins": histo_bins}


def _nnlojet_observable(observable, process):
    """Try to automatically understand the NNLOJET observables given the NNPDF process and obs."""
    observable = observable.lower()
    if observable in ("eta", "y", "etay"):
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
    if observable == "m" and process.upper().startswith("Z"):
        return "mll"
    if observable == "m2":
        print("\033[91m [WARNING] \033[0m Changed M2 to M in the selectors")
        return "mll"

    raise ValueError(f"Observable {observable} not recognized for process {process}")


def _generate_metadata(arxiv, hepdata, nnpdf_name, output):
    """Generate a minimal ``metadata.txt`` file."""
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
    """A selection of default selectors to be selected depending on the selected experiment.

    The experiment defines the cuts to be applied to each variable.
    The process defines the name of the variables in NNLOJET
    """
    cuts = {
        "rapidity": (None, None),
        "pt": (20.0, None),
        "inv_mass": (None, None),
        "mt": (None, None),
    }

    variables = {"rapidity": [], "pt": [], "inv_mass": [], "mt": []}

    if experiment == "LHCB":
        cuts["rapidity"] = (2.0, 4.5)
        cuts["inv_mass"] = (60.0, 120.0)
    elif experiment == "ATLAS":
        cuts["rapidity"] = (0.0, 2.5)
        cuts["inv_mass"] = (66.0, 116.0)
        cuts["pt"] = (25.0, None)
        cuts["mt"] = (50.0, None)
    elif experiment == "CMS":
        cuts["rapidity"] = (0.0, 2.4)
        cuts["inv_mass"] = (60.0, 120.0)
        cuts["pt"] = (35.0, None)
    else:
        raise NotImplementedError(f"Selectors for {experiment=} not implemented")

    if process.startswith("Z"):
        variables["rapidity"] += ["yz", "abs_ylp", "abs_ylm"]
        variables["inv_mass"].append("mll")
        variables["pt"].append("ptl2")
    elif process.startswith("W"):
        w_sign = process[1].lower()
        variables["rapidity"].append(f"abs_yl{w_sign}")
        variables["pt"].append(f"ptl{w_sign}")
        variables["mt"].append("mt")

    selector_options = []

    for cut_type, (cut_min, cut_max) in cuts.items():

        if cut_min is None and cut_max is None:
            continue

        for variable in variables[cut_type]:
            tmp = {"observable": variable}
            if cut_min is not None:
                tmp["min"] = cut_min
            if cut_max is not None:
                tmp["max"] = cut_max

            selector_options.append(tmp)

    return selector_options


def _generate_nnlojet_pinecard(runname, process, energy, experiment, histograms):
    """Generate a pinecard for NNLOJET runs from an NNPDF dataset."""
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


def generate_pinecard_from_nnpdf(
    nnpdf_dataset, scale="etz", output_path=".", observables=None
):
    """Generate a NNLOJET pinecard from an NNPDF dataset.

    Takes as input an NNPDF dataset, which will be loaded with the
    nnpdf_data package.

    If a list of observables is provided, only those in the list will be loaded
    from the dataframe.
    """
    metadata = load_dataset_metadata(nnpdf_dataset)
    kin_df = metadata.load_kinematics(drop_minmax=False)

    if observables is not None:
        # If a list of observables is provided, select them from the dataframe
        # list in case they enter as a tuple
        kin_df = kin_df.loc[:, list(observables)]

    # Change some variable names:
    kin_df.rename(columns={"m_ll2": "M2"}, inplace=True)
    output_runcards = []

    # Put all the information we might need in nicely organized variables
    process = metadata.process
    energy = metadata.cm_energy
    experiment = metadata.experiment

    # Now use the kinematic information to generate histograms
    kin_variables = kin_df.columns.get_level_values(0)

    # Is it legacy?
    if "k1" in kin_variables:
        # Time to translate!
        _legacy_nnpdf_translation(kin_df, metadata.process_type)
        kin_variables = kin_df.columns.get_level_values(0)

    hist_vars = list(HISTOGRAM_VARIABLES.intersection(kin_variables))

    # Now preprocess the variables according to the process type

    # Drell Yan
    if process in ("WPWM", "Z0", "DY"):
        # Special case: is a histogram binned by invariant mass?
        if "M2" in hist_vars:
            if len(kin_df["M2"]["mid"].unique()) == 1:
                hist_vars.remove("M2")

    # Create the histogram depending on whether this is a 1D or 2D distribution (or total)
    histograms = None

    if len(hist_vars) == 1:
        histograms = [_1d_histogram(kin_df, hist_vars[0])]
    elif len(hist_vars) == 2:

        # Let's see whether we know how to do this 2D distribution
        if "M2" in hist_vars:
            svar = "M2"
        elif "y" in hist_vars:
            svar = "y"
        else:
            raise NotImplementedError(f"Don't know how to do this 2D: {hist_vars}")
        hist_vars.remove(svar)

        # 2D distributions can only be done when min-max is available, otherwise it's a mess
        bounds_df = kin_df[svar]
        if svar.endswith("2"):
            bounds_df[["min", "max"]] = bounds_df[["min", "max"]].apply(
                lambda x: np.sqrt(x)
            )
        bounds = bounds_df.drop_duplicates().values.tolist()

        nnlojet_var = _nnlojet_observable(svar, process)
        another_v = hist_vars[0]
        histograms = []

        for i, (bin_min, mid_val, bin_max) in enumerate(bounds):
            idx = kin_df[svar]["mid"] == mid_val
            tmp = _1d_histogram(kin_df[idx], another_v)
            tmp["name"] = f"{another_v}_bin_{i}"
            tmp["extra_selectors"] = [
                {
                    "observable": f"{nnlojet_var}",
                    "min": bin_min,
                    "max": bin_max,
                }
            ]
            histograms.append(tmp)
    elif len(hist_vars) == 0 and metadata.process_type == "INC":
        # inclusive cross section, just create a big enough histogram
        histograms = [{"observable": "y", "bins": [-10.0, 10.0], "name": "tot"}]
    else:
        raise NotImplementedError(
            "3D distributions not implemented or process not recognized"
        )

    is_normalized = metadata.theory.operation.lower() == "ratio"
    if is_normalized:
        print(
            "\033[91m [WARNING] \033[0m This dataset is probably normalized, you might be missing the runcard for the fiducial cross section"
        )

    # Prepare the metadata for the data
    hepdata = metadata._parent.hepdata.url
    arxiv = metadata._parent.arXiv.url.split("/")[-1]
    tables = metadata.tables
    if not hepdata.startswith("https:"):
        # Try to autoguess the doi
        hepdata = f"https://doi.org/{hepdata}"

    data_comment = f"arXiv number: {arxiv}, hepdata entry: {hepdata} (tables: {tables})"
    print(
        f"\033[91m [WARNING] \033[0m Remember to update he selection cuts in the runcard, see {hepdata}"
    )

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
