#!/usr/bin/env python3

"""
A Python script that takes a Grid binned in Rapidity and perform the following operations:
    - extract the negative rapidity bins and divide the observable predictions by 2
    - extract the positive rapidity bins and divide the observable predictions by 2
    - re-order the negative rapidity bin predictions to conform with the commondata
    - merge the two Grids

To use, check `python ./matrix_yttbar.py --help`, or directly run:
    `python ./matrix_yttbar.py -g <path_to_grid> -o <output_name>`

To run the check, use `pytest`:
    `pytest ./matrix_yttbar.py`
"""
import numpy as np
import pineappl
import rich_click as click
import subprocess


class InvalidPineAPPL(Exception):
    """Check whether the PineAPPL version is valid."""

    pass


class TestReverseBins:
    def fake_grid(self, bins=None) -> pineappl.grid.Grid:
        """Generate a fake PineAPPL grid."""
        lumis = [pineappl.lumi.LumiEntry([(1, i, 1)]) for i in range(-3, 3)]
        orders = [pineappl.grid.Order(i, 0, 0, 0) for i in range(3)]
        binning = np.array([1e-7, 1e-3] if bins is None else bins, dtype=float)

        subgrid_params = pineappl.subgrid.SubgridParams()
        grid = pineappl.grid.Grid.create(lumis, orders, binning, subgrid_params)

        # Fill the Grid with some random weights
        for b in range(binning.size - 1):
            for o in range(len(orders)):
                for c in range(len(lumis)):
                    x1s = np.logspace(0.1, 1, num=10)
                    x2s = np.logspace(0.5, 1, num=10)
                    q2s = np.logspace(10, 20, num=10)
                    sub_array = np.random.uniform(
                        2, 6, size=(q2s.size, x1s.size, x2s.size)
                    )
                    mu2_scales = [(q2, q2) for q2 in q2s]
                    subgrid_obj = pineappl.import_only_subgrid.ImportOnlySubgridV2(
                        array=sub_array,
                        mu2_grid=mu2_scales,
                        x1_grid=x1s,
                        x2_grid=x2s,
                    )
                    grid.set_subgrid(o, b, c, subgrid=subgrid_obj)

        return grid

    def test_reverse_bins(self):
        ref_grid = self.fake_grid(bins=[0.5, 1.0, 1.5, 2.0])
        mod_grid = reverse_bins(grid=ref_grid)

        # Convolve the Grids with some fake PDFs
        ref_preds = ref_grid.convolve_with_one(
            pdg_id=2212,
            xfx=lambda pid, x, q2: x,
            alphas=lambda q2: 1.0,
        )
        mod_preds = mod_grid.convolve_with_one(
            pdg_id=2212,
            xfx=lambda pid, x, q2: x,
            alphas=lambda q2: 1.0,
        )
        # NOTE: predictions are expected to differ by `1/2`
        np.testing.assert_allclose(ref_preds / 2, mod_preds[::-1])


def check_obsdims(grid: pineappl.grid.Grid) -> None:
    """Check that the observable is binned in one dimension only."""
    assert (
        grid.bin_dimensions() == 1
    ), "The observable is binned in multiple dimensions."
    return


def modify_grids(
    grid: pineappl.grid.Grid, positive_sign: bool = True, norm: float = 1.0
) -> None:
    """Rewrite the bin and observable contents of the Grid"""
    sign: int = 1 if positive_sign else (-1)
    modified_rap_bins = [
        (sign * float(left) if left != 0.0 else float(left), sign * float(right))
        for left, right in zip(grid.bin_left(0), grid.bin_right(0))
    ]

    remapper = pineappl.bin.BinRemapper(
         grid.bin_normalizations(), modified_rap_bins
    )
    grid.set_remapper(remapper)
    return


def reverse_bins(grid: pineappl.grid.Grid) -> pineappl.grid.Grid:
    """Reverse the order of the bins for a given Grid."""
    n_channels = len(grid.channels())
    n_bins = grid.bins()
    n_orders = len(grid.orders())

    # Init a new Grid to store the reversed predictions
    reversed_bins = np.append(grid.bin_right(0)[-1], grid.bin_left(0)[::-1])
    new_grid = pineappl.grid.Grid.create(
        [pineappl.lumi.LumiEntry(c) for c in grid.channels()],
        grid.orders(),
        reversed_bins,
        pineappl.subgrid.SubgridParams(),
    )

    # Collect the different subgrids at a given `boc`
    inv_bindex = [i for i in range(n_bins)]
    for b in range(n_bins):
        for o in range(n_orders):
            for c in range(n_channels):
                bb = inv_bindex[-(b + 1)]
                subgrid = grid.subgrid(o, bb, c)
                mu2_scales = [(mu2.ren, mu2.fac) for mu2 in subgrid.mu2_grid()]
                x1_grid = subgrid.x1_grid()
                x2_grid = subgrid.x2_grid()
                sub_array = subgrid.to_array3()

                subgrid_obj = pineappl.import_only_subgrid.ImportOnlySubgridV2(
                    array=sub_array,
                    mu2_grid=mu2_scales,
                    x1_grid=x1_grid,
                    x2_grid=x2_grid,
                )
                new_grid.set_subgrid(o, b, c, subgrid=subgrid_obj)

    # Fix back the normalization - Infer from the original Grid
    modify_grids(grid=new_grid, positive_sign=True, norm=2.0)
    return new_grid


def merge_bins(
    grid1: pineappl.grid.Grid, grid2: pineappl.grid.Grid, outname: str
) -> None:
    """Merge two grids with different bins"""
    grid1.merge(grid2)
    return grid1



@click.command()
@click.option(
    "--grid_path",
    "-g",
    type=click.Path(exists=True),
    required=True,
    help="Path to the starting Grid.",
)
@click.option(
    "--output_name",
    "-o",
    required=True,
    help="Name of the output Grid (w/o the extension `pineappl.lz4`).",
)
def main(grid_path: str, output_name: str) -> None:
    grid_pos = pineappl.grid.Grid.read(grid_path)  # For positive rapidity bins
    grid_neg = pineappl.grid.Grid.read(grid_path)  # For negative rapidity bins
    check_obsdims(grid_pos)

    # Modify the bin and observable contents of the Grids
    modify_grids(grid=grid_pos, positive_sign=True, norm=2.0)
    modify_grids(grid=grid_neg, positive_sign=False, norm=2.0)

    # Revert the bin ordering of the negative rapidity Grid
    modified_grid = reverse_bins(grid=grid_neg)

    merged_grid = merge_bins(grid1=modified_grid, grid2=grid_pos, outname=output_name)

    merged_grid.write_lz4(f"{output_name}_temp.pineappl.lz4")
    subprocess.run(["pineappl", "write", "--scale", "0.5", f"{output_name}_temp.pineappl.lz4", f"{output_name}.pineappl.lz4"])
    subprocess.run(["rm", f"{output_name}_temp.pineappl.lz4"])
    return


if __name__ == "__main__":
    if pineappl.__version__ != "0.8.7":
        raise InvalidPineAPPL("The PineAPPL version is not compatible.")
    main()