"""yadism interface."""

from functools import reduce

import pandas as pd
import yadbox.export
import yadism
import yadism.output
import yaml

from .. import configs, log, tools
from . import interface


class Yadism(interface.External):
    """Interface provider."""

    kind = "DIS"

    def __init__(self, pinecard, theorycard, *args, **kwargs):
        # Default to including scale information unless explicitly avoided
        theorycard.setdefault("FactScaleVar", True)
        theorycard.setdefault("RenScaleVar", True)

        super().__init__(pinecard, theorycard, *args, **kwargs)

        # load runcards
        with open(
            configs.configs["paths"]["runcards"] / self.name / "observable.yaml"
        ) as o:
            self.obs = yaml.safe_load(o)

        # deactivate TMC for positivity observables
        # (see also minutes of 2022-07-29)
        if self.obs["NCPositivityCharge"] is not None:
            self.theory["TMC"] = 0

    @property
    def output(self):
        """Return yadism output path."""
        return self.grid.with_suffix(".tar")

    def run(self):
        """Run program."""
        print("Running yadism...")

        # run yadism
        run_log = self.dest / "run.log"
        with log.Tee(run_log, stderr=True):
            try:
                out = yadism.run_yadism(self.theory, self.obs)
            except Exception:
                raise log.WhileRedirectedError(file=run_log)

        # dump output
        out.dump_tar(self.output)

    def generate_pineappl(self):
        """Generate grid."""
        out = yadism.output.Output.load_tar(self.output)
        yadbox.export.dump_pineappl_to_file(
            out, str(self.grid), next(iter(self.obs["observables"].keys()))
        )

    def results(self):
        """Apply PDF to output."""
        import lhapdf  # pylint: disable=import-error

        pdf = lhapdf.mkPDF(self.pdf)
        out = yadism.output.Output.load_tar(self.output)
        pdf_out = out.apply_pdf_alphas_alphaqed_xir_xif(
            pdf,
            lambda muR: lhapdf.mkAlphaS(self.pdf).alphasQ(muR),
            lambda _muR: 0,
            1.0,
            1.0,
        )
        pdf_out = next(iter(pdf_out.tables.values()))

        sv_pdf_out = []
        for xiR, xiF in tools.nine_points:
            sv_point = out.apply_pdf_alphas_alphaqed_xir_xif(
                pdf,
                lambda muR: lhapdf.mkAlphaS(self.pdf).alphasQ(muR),
                lambda _muR: 0.0,
                xiR,
                xiF,
            )
            df = (
                next(iter(sv_point.tables.values()))
                .rename({"result": (xiR, xiF)}, axis=1)
                .drop("error", axis=1)
            )
            if len(sv_pdf_out) > 0:
                df.drop(
                    [col for col in df if col in sv_pdf_out[0]], axis=1, inplace=True
                )
            sv_pdf_out.append(df)

        sv_pdf_merged = reduce(
            lambda left, right: pd.merge(
                left,
                right,
                left_index=True,
                right_index=True,
                validate="one_to_one",
            ),
            sv_pdf_out,
        )
        svdf = sv_pdf_merged[
            list(filter(lambda name: isinstance(name, tuple), sv_pdf_merged.columns))
        ]
        pdf_out["sv_max"] = svdf.max(axis=1)
        pdf_out["sv_min"] = svdf.min(axis=1)

        return pdf_out

    def collect_versions(self):
        """No additional programs involved."""
        return {}
