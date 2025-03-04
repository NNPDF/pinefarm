MATRIX
======


Post-processing grids
---------------------

We need to post-process the raw grids outputted by MATRIX -
use one of the available interfaces (including the CLI) to do so.


- **Optimize and scale:** apply the built-in optimization and rescaled by a factor if needed to go e.g. from pb to fb.

- **Delete keys:** delete `y_label_unit`, `xlabel` and `x_label-tex`

- **Add keys:**
    .. list-table:: Additional keys
        :widths: 25 25 50
        :header-rows: 1

        * - key
          - value
          - comment
        * - y-unit
          - pb/GeV
          -
        * - y-label
          - differential x-sec
          -
        * - lumi_id_types
          - pdg_mc_ids
          - needed for compatibility with LHAPDF
        * - arxiv
          -
          - put the original paper

- **Add output log of MATRIX:** put the original MATRIX output log under the `results` key as usual
