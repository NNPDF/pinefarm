#!/usr/bin/env python3

"""
A Python script that takes a Grid binned in Rapidity and perform the following operations:
    - extract the negative rapidity bins and divide the observable predictions by 2
    - extract the positive rapidity bins and divide the observable predictions by 2
    - re-order the negative rapidity bin predictions to conform with the commondata
    - merge the two Grids

To use, check `python ./matrix_yttbar.py --help`, or directly run:
    `python ./matrix_yttbar.py -g <path_to_grid> -o <output_name>`
"""
import numpy as np
import pineappl
import rich_click as click


class InvalidPineAPPL(Exception):
    """Check whether the PineAPPL version is valid."""

    pass


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
        (float(left), float(right))
        for left, right in zip(sign * grid.bin_left(0), sign * grid.bin_right(0))
    ]

    remapper = pineappl.bin.BinRemapper(
        norm * grid.bin_normalizations(), modified_rap_bins
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
    grid1.write_lz4(f"{outname}.pineappl.lz4")
    return


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

    merge_bins(grid1=modified_grid, grid2=grid_pos, outname=output_name)
    return


if __name__ == "__main__":
    if pineappl.__version__ != "0.8.7":
        raise InvalidPineAPPL("The PineAPPL version is not compatible.")
    main()
